"""
This file defines the Interpreter class, which is the main class for the interpreter module.
When you `import interpreter`, you are actually importing an instance of this class.
"""
from interpreter.utils import display_markdown_message

from concurrent.futures import ThreadPoolExecutor
import json
import os
from datetime import datetime
from ..cli.cli import cli
from ..llm.setup_llm import setup_llm
from ..rag.get_relevant_procedures_string import get_relevant_procedures_string
from ..terminal_interface.terminal_interface import terminal_interface
from ..terminal_interface.validate_llm_settings import validate_llm_settings
from ..utils.check_for_update import check_for_update
from ..utils.display_markdown_message import display_markdown_message
from ..utils.embed import embed_function
from ..utils.get_config import get_config, user_config_path
from ..utils.local_storage_path import get_storage_path
from .generate_system_message import generate_system_message
from .respond import respond
from interpreter.poe_api import PoeAPI

class Interpreter:
    """
    The Interpreter class is responsible for managing the state and settings of the interpreter.
    It also provides methods for interacting with the interpreter via the command line interface (CLI).
    """
    def cli(self):
        """
        This method starts the command line interface (CLI) for the interpreter.
        """
        cli(self)

    def __init__(self):
        """
        Initializes the Interpreter with default state and settings.
        """
        # State
        self.messages = []  # List to store messages
        self._code_interpreters = {}  # Dictionary to store code interpreters

        # Configuration file path
        self.config_file = user_config_path

        # Settings
        self.local = False  # Flag to indicate if the interpreter should run locally
        self.auto_run = False  # Flag to indicate if the interpreter should run automatically
        self.debug_mode = False  # Flag to indicate if the interpreter should run in debug mode
        self.max_output = 2000  # Maximum output length
        self.safe_mode = "off"  # Safety mode setting

        # Conversation history
        self.conversation_history = True
        self.conversation_filename = None
        self.conversation_history_path = get_storage_path("conversations")

        # LLM settings
        self.model = ""
        self.temperature = None
        self.system_message = ""
        self.context_window = None
        self.max_tokens = None
        self.api_base = None
        self.api_key = None
        self.max_budget = None
        self._llm = None
        self.gguf_quality = None

        # Procedures / RAG
        self.procedures = None
        self._procedures_db = {}
        self.download_open_procedures = True
        self.embed_function = embed_function
        self.executor = ThreadPoolExecutor(max_workers=5)
        # Number of procedures to add to the system message
        self.num_procedures = 2

        # Load config defaults
        self.extend_config(self.config_file)

        # Check for update
        if not self.local:
            # This should actually be pushed into the utility
            if check_for_update():
                display_markdown_message(
                    "> **A new version of Open Interpreter is available.**\n>Please run: `pip install --upgrade open-interpreter`\n\n---"
                )

    def extend_config(self, config_path):
        if self.debug_mode:
            print(f"Extending configuration from `{config_path}`")

        config = get_config(config_path)
        self.__dict__.update(config)

    def chat(self, message=None, display=True, stream=False):
        """
        This method starts a chat session. If stream is True, it returns a generator that yields chat messages.
        If stream is False, it pulls all messages from the stream and returns them as a list.

        Args:
            message (str, optional): An initial message to start the chat session. Defaults to None.
            display (bool, optional): A flag indicating whether to display the chat messages. Defaults to True.
            stream (bool, optional): A flag indicating whether to return a stream of chat messages. Defaults to False.

        Returns:
            list or generator: A list or stream of chat messages.
        """
        if stream:
            return self._streaming_chat(message=message, display=display)

        # If stream=False, *pull* from the stream.
        for _ in self._streaming_chat(message=message, display=display):
            pass

        return self.messages
      
    def _streaming_chat(self, message=None, display=True):
        """
        This method starts a streaming chat session. It returns a generator that yields chat messages.

        Args:
            message (str, optional): An initial message to start the chat session. Defaults to None.
            display (bool, optional): A flag indicating whether to display the chat messages. Defaults to True.

        Returns:
            generator: A stream of chat messages.
        """
        with ThreadPoolExecutor() as executor:
            # If we have a display, we can validate our LLM settings w/ the user first
            if display:
                executor.submit(validate_llm_settings, self)

            # Setup the LLM
            if not self._llm:
                self._llm = executor.submit(setup_llm, self).result()

            # Sometimes a little more code -> a much better experience!
            # Display mode actually runs interpreter.chat(display=False, stream=True) from within the terminal_interface.
            # wraps the vanilla .chat(display=False) generator in a display.
            # Quite different from the plain generator stuff. So redirect to that
            if display:
                yield from executor.submit(terminal_interface, self, message).result()
                return

        # One-off message
        if message or message == "":
            if message == "":
                message = "No entry from user - please suggest something to enter"
            self.messages.append({"role": "user", "message": message})
            self.safe_mode = "off"
            self.poe_api = PoeAPI()  # Initialize the PoeAPI
            response = self.poe_api.get_endpoint('actual_endpoint')  # Replace with actual endpoint
            # Handle the response
            data = json.loads(response)
            # Use the data in the application
            # Implement logic to use data in the application
            self.use_data(data)
            yield from future.result()
    
                # Save conversation if we've turned conversation_history on
            if self.conversation_history:
                # If it's the first message, set the conversation name
                if not self.conversation_filename:
                    first_few_words = "_".join(
                        self.messages[0]["message"][:25].split(" ")[:-1]
                    )
                    for char in '<>:"/\\|?*!':  # Invalid characters for filenames
                        first_few_words = first_few_words.replace(char, "")

                    date = datetime.now().strftime("%B_%d_%Y_%H-%M-%S")
                    self.conversation_filename = (
                        "__".join([first_few_words, date]) + ".json"
                    )

                # Check if the directory exists, if not, create it
                if not os.path.exists(self.conversation_history_path):
                    os.makedirs(self.conversation_history_path)
                # Write or overwrite the file
                with open(
                    os.path.join(
                        self.conversation_history_path, self.conversation_filename
                    ),
                    "w",
                ) as f:
                    json.dump(self.messages, f)

            return
        raise Exception(
            "`interpreter.chat()` requires a display. Set `display=True` or pass a message into `interpreter.chat(message)`."
        )

    def _respond(self):
        yield from respond(self)

    def reset(self):
        with ThreadPoolExecutor() as executor:
            for code_interpreter in self._code_interpreters.values():
                executor.submit(code_interpreter.terminate)
            self._code_interpreters = {}

        # Use the PoeAPI instance to make requests to the PoE API and handle the responses
        # This is a placeholder and should be replaced with the actual logic for making requests and handling responses
        response = self.poe_api.get_endpoint('actual_endpoint')  # Replace with actual endpoint
        # Handle the response
        data = json.loads(response)
        # Use the data in the application
        self.use_data(data)
        
        def use_data(self, data):
        """
        This method handles the data received from the PoE API.
        The exact implementation of this function will depend on the specific needs of the application.

        Args:
            data (dict): The data received from the PoE API.
        """
        # For example, if the data is a dictionary, you can access its elements like this:
        element = data['key']  # Replace with actual key
        # Then you can use the element in your application
        # Implement logic to use element in the application
        pass
        def use_data(self, data):
            # Handle the data received from the PoE API
            # The exact implementation of this function will depend on the specific needs of the application
            # Implement logic to handle data
            print(data)

    def reset(self):
        for code_interpreter in self._code_interpreters.values():
            code_interpreter.terminate()
        self.executor.shutdown(wait=True)
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._code_interpreters = {}

        # Reset the two functions below, in case the user set them
        self.generate_system_message = lambda: generate_s
            self.__init__()

    # These functions are worth exposing to developers
    # I wish we could just dynamically expose all of our functions to devs...
    def generate_system_message(self):
        return generate_system_message(self)

    def get_relevant_procedures_string(self):
        return get_relevant_procedures_string(self)

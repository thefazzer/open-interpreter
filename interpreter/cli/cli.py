import argparse
import subprocess
import os
import platform
import pkg_resources
import ooba
from ..utils.get_config import get_config_path
from ..terminal_interface.conversation_navigator import conversation_navigator

arguments = [
    {
        "name": "system_message",
        "nickname": "s",
        "help_text": "prompt / custom instructions for the language model",
        "type": str,
    },
    {"name": "local", "nickname": "l", "help_text": "Run the language model locally (experimental)", "type": bool},
    {
        "name": "auto_run",
        "nickname": "y",
        "help_text": "Automatically run the interpreter",
        "type": bool,
    },
    {
        "name": "debug_mode",
        "nickname": "d",
        "help_text": "Run in debug mode",
        "type": bool,
    },
    {
        "name": "model",
        "nickname": "m",
        "help_text": "Specify the model to use for the language model",
        "type": str,
    },
    {
        "name": "temperature",
        "nickname": "t",
        "help_text": "Set the temperature for the language model (optional)",
        "type": float,
    },
    {
        "name": "context_window",
        "nickname": "c",
        "help_text": "Set the context window size for the language model (optional)",
        "type": int,
    },
    {
        "name": "max_tokens",
        "nickname": "x",
        "help_text": "Set the maximum number of tokens for the language model (optional)",
        "type": int,
    },
    {
        "name": "max_budget",
        "nickname": "b",
        "help_text": "Set the max budget (in USD) for your llm calls (optional)",
        "type": float,
    },
    {
        "name": "api_base",
        "nickname": "ab",
        "help_text": "Set the API base URL for your llm calls (optional, overrides environment variables)",
        "type": str,
    },
    {
        "name": "api_key",
        "nickname": "ak",
        "help_text": "Set the API key for your llm calls (optional, overrides environment variables)",
        "type": str,
    },
    {
        "name": "safe_mode",
        "nickname": "safe",
        "help_text": "Enable safety mechanisms like code scanning (optional, valid options are off, ask, and auto)",
        "type": str,
        "choices": ["off", "ask", "auto"],
    },
    {
        "name": "gguf_quality",
        "nickname": "q",
        "help_text": "Set the gguf quality/quantization level (experimental, value from 0-1, lower = smaller, faster, more quantized)",
        "type": float,
    },
    {
        "name": "config_file",
        "nickname": "cf",
        "help_text": "Set a custom config file to use (optional)",
        "type": str,
    },
]


def cli(interpreter):
    parser = argparse.ArgumentParser(description="Open Interpreter")

    # Add arguments
    for arg in arguments:
        if arg["type"] == bool:
            parser.add_argument(
                f'-{arg["nickname"]}',
                f'--{arg["name"]}',
                dest=arg["name"],
                help=arg["help_text"],
                action="store_true",
                default=None,
            )
        else:
            choices = arg["choices"] if "choices" in arg else None
            default = arg["default"] if "default" in arg else None

            parser.add_argument(
                f'-{arg["nickname"]}',
                f'--{arg["name"]}',
                dest=arg["name"],
                help=arg["help_text"],
                type=arg["type"],
                choices=choices,
                default=default,
            )

    # Add special arguments
    parser.add_argument(
        "--config",
        dest="config",
        action="store_true",
        help="open config.yaml file in text editor",
    )
    parser.add_argument(
        "--conversations",
        dest="conversations",
        action="store_true",
        help="list conversations to resume",
    )
    # The --fast argument is deprecated and should not be used
    parser.add_argument(
        "--version",
        dest="version",
        action="store_true",
        help="get Open Interpreter's version number",
    )
    parser.add_argument(
        '--change_local_device',
        dest='change_local_device',
        action='store_true',
        help="change the device used for local execution (if GPU fails, will use CPU)"
    )

    # TODO: Implement model explorer
    # parser.add_argument('--models', dest='models', action='store_true', help='list avaliable models')

    args = parser.parse_args()

    # This should be pushed into an open_config.py util
    # If --config is used, open the config.yaml file in the Open Interpreter folder of the user's config dir
    if args.config:
        if args.config_file:
            config_file = get_config_path(args.config_file)
        else:
            config_file = get_config_path()

        print(f"Opening `{config_file}`...")

        # Use the default system editor to open the file
        if platform.system() == "Windows":
            os.startfile(
                os.path.abspath(config_file)
            )  # This will open the file with the default application, e.g., Notepad
        else:
            try:
                # Try using xdg-open on non-Windows platforms
                if "xdg-open" in ["xdg-open", "open"]:
                    subprocess.call(["xdg-open", os.path.abspath(config_file)])
            except FileNotFoundError:
                # Fallback to using 'open' on macOS if 'xdg-open' is not available
                if "open" in ["xdg-open", "open"]:
                    subprocess.call(["open", os.path.abspath(config_file)])
        return

    # TODO Implement model explorer
    """
    # If --models is used, list models
    if args.models:
        # If they pick a model, set model to that then proceed
        args.model = model_explorer()
    """

    # Set attributes on interpreter
    for attr_name, attr_value in vars(args).items():
        # Ignore things that aren't possible attributes on interpreter
        if attr_value is not None and hasattr(interpreter, attr_name):
            # If the user has provided a config file, load it and extend interpreter's configuration
            if attr_name == "config_file":
                user_config = get_config_path(attr_value)
                interpreter.config_file = user_config
                interpreter.extend_config(config_path=user_config)
            else:
                interpreter.attr_name = attr_value

    # if safe_mode and auto_run are enabled, safe_mode disables auto_run
    if interpreter.auto_run and not interpreter.safe_mode == "off":
        interpreter.auto_run = False

    # Default to Mistral if --local is on but --model is unset
    if interpreter.local and args.model is None:
        # This will cause the terminal_interface to walk the user through setting up a local LLM
        interpreter.model = ""

    # If --conversations is used, run conversation_navigator
    if args.conversations:
        conversation_navigator(interpreter)
        return

    if args.version:
        version = pkg_resources.get_distribution("open-interpreter").version
        print(f"Open Interpreter {version}")
        return

    if args.change_local_device:
        print("This will uninstall the experimental local LLM interface (Ooba) in order to reinstall it for a new local device. Proceed? (y/n)")
        if input().lower() == "n":
            return

        print("Please choose your GPU:\n")

        print("A) NVIDIA")
        print("B) AMD (Linux/MacOS only. Requires ROCm SDK 5.4.2/5.4.3 on Linux)")
        print("C) Apple M Series")
        print("D) Intel Arc (IPEX)")
        print("N) None (I want to run models in CPU mode)\n")

        gpu_choice = input("> ").upper()

        while gpu_choice not in 'ABCDN':
            print("Invalid choice. Please try again.")
            gpu_choice = input("> ").upper()

        ooba.install(force_reinstall=True, gpu_choice=gpu_choice, verbose=args.debug_mode)
        return

    # The --fast argument is deprecated and should not be used

    interpreter.chat()

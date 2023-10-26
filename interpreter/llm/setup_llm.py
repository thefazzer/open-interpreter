from concurrent.futures import ThreadPoolExecutor
import litellm
from .setup_text_llm import setup_text_llm
from .convert_to_coding_llm import convert_to_coding_llm
from .setup_openai_coding_llm import setup_openai_coding_llm
from .setup_text_llm import setup_text_llm


def setup_llm(interpreter):
    """
    This function takes an Interpreter instance, which includes various settings for the Language Learning Model (LLM),
    and returns a Coding LLM. The Coding LLM is a generator that streams deltas with `message` and `code`.
    """

    with ThreadPoolExecutor() as executor:
        if not interpreter.local and (
            interpreter.model in litellm.open_ai_chat_completion_models
            or interpreter.model.startswith("azure/")
        ):
            # Submit a task to the executor to setup the OpenAI coding LLM
            coding_llm_future = executor.submit(setup_openai_coding_llm, interpreter)
        else:
            # Submit a task to the executor to setup the text LLM
            text_llm_future = executor.submit(setup_text_llm, interpreter)
            # Convert the text LLM to a coding LLM
            coding_llm_future = executor.submit(
                convert_to_coding_llm,
                text_llm_future.result(),
                debug_mode=interpreter.debug_mode,
            )

        # Wait for the coding LLM setup to complete and get the result
        coding_llm = coding_llm_future.result()
    return coding_llm

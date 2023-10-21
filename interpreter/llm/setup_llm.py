from .setup_text_llm import setup_text_llm
from .convert_to_coding_llm import convert_to_coding_llm
from .setup_openai_coding_llm import setup_openai_coding_llm
from concurrent.futures import ThreadPoolExecutor
import litellm

def setup_llm(interpreter):
    """
    Takes an Interpreter (which includes a ton of LLM settings),
    returns a Coding LLM (a generator that streams deltas with `message` and `code`).
    """

    with ThreadPoolExecutor() as executor:
        if (not interpreter.local
            and (interpreter.model in litellm.open_ai_chat_completion_models or interpreter.model.startswith("azure/"))):
            # Function calling LLM
            coding_llm_future = executor.submit(setup_openai_coding_llm, interpreter)
        else:
            text_llm_future = executor.submit(setup_text_llm, interpreter)
            coding_llm_future = executor.submit(convert_to_coding_llm, text_llm_future.result(), debug_mode=interpreter.debug_mode)

        coding_llm = coding_llm_future.result()

    return coding_llm
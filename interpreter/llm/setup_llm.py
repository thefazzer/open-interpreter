from .setup_text_llm import setup_text_llm
from .convert_to_coding_llm import convert_to_coding_llm
from .setup_openai_coding_llm import setup_openai_coding_llm
import os
import litellm

def setup_llm(interpreter):
    """
    Takes an Interpreter (which includes a ton of LLM settings),
    returns a Coding LLM (a generator that streams deltas with `message` and `code`).
    """

    if (not interpreter.local
        and (interpreter.model in litellm.open_ai_chat_completion_models or interpreter.model.startswith("azure/"))):
        # Function calling LLM
        future = executor.submit(setup_openai_coding_llm, interpreter)
        coding_llm = future.result()
    else:
        future1 = executor.submit(setup_text_llm, interpreter)
        text_llm = future1.result()
        executor = ThreadPoolExecutor(max_workers=5)
        future2 = executor.submit(convert_to_coding_llm, text_llm, debug_mode=interpreter.debug_mode)
        coding_llm = future2.result()

    return coding_llm
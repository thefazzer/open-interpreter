import os
from secrets import randbelow
from random import randint
import pytest
from pytest import mark
import pytest_xdist
import interpreter
from interpreter.utils.count_tokens import count_tokens, count_messages_tokens

interpreter.auto_run = True
interpreter.model = "gpt-4"
interpreter.temperature = 0


# this function will run before each test
# we're clearing out the messages Array so we can start fresh and reduce token usage
def setup_function():
    interpreter.reset()
    interpreter.temperature = 0
    interpreter.auto_run = True
    interpreter.model = "gpt-4"
    interpreter.debug_mode = False


# this function will run after each test
# we're introducing some sleep to help avoid timeout issues with the OpenAI API
def teardown_function():
    time.sleep(5)


@mark.parametrize("config_path", ["./config.test.yaml"])
def test_config_loading(config_path):
    # Because our test is running from the root directory, we need to do some
    # path manipulation to get the actual path to the config file or our config
    # loader will try to load from the wrong directory and fail
    currentPath = os.path.dirname(os.path.abspath(__file__))
    config_path=os.path.join(currentPath, './config.test.yaml')

    interpreter.extend_config(config_path=config_path)

    # check the settings we configured in our config.test.yaml file
    temperature_ok = interpreter.temperature == 0.8
    model_ok = interpreter.model == "gpt-3.5-turbo"
    debug_mode_ok = interpreter.debug_mode
    if not (temperature_ok and model_ok and debug_mode_ok):
        raise AssertionError()

@mark.parametrize("ping_request, pong_response", [("ping", "pong")])
def test_system_message_appending(ping_request, pong_response):
    ping_system_message = "Respond to a `ping` with a `pong`. No code. No explanations. Just `pong`."

    ping_request = "ping"
    pong_response = "pong"

    interpreter.system_message += ping_system_message

    messages = interpreter.chat(ping_request)

    assert messages == [
        {"role": "user", "message": ping_request},
        {"role": "assistant", "message": pong_response},
    ]


@mark.parametrize("messages", [[]])
def test_reset(messages):
    # Make sure that interpreter.reset() clears out the messages Array
    if not interpreter.messages == messages:
        raise AssertionError()

@mark.parametrize("system_message, prompt", [(interpreter.system_message, "How many tokens is this?")])
def test_token_counter(system_message, prompt):
    system_tokens = count_tokens(text=interpreter.system_message, model=interpreter.model)
    
    prompt = "How many tokens is this?"

    prompt_tokens = count_tokens(text=prompt, model=interpreter.model)

    messages = [{"role": "system", "message": interpreter.system_message}] + interpreter.messages

    system_token_test = count_messages_tokens(messages=messages, model=interpreter.model)

    system_tokens_ok = system_tokens == system_token_test[0]

    messages.append({"role": "user", "message": prompt})

    prompt_token_test = count_messages_tokens(messages=messages, model=interpreter.model)

    prompt_tokens_ok = system_tokens + prompt_tokens == prompt_token_test[0]

    if not (system_tokens_ok and prompt_tokens_ok):
        raise AssertionError()


@mark.parametrize("hello_world_message", ["Please reply with just the words Hello, World! and nothing else. Do not run code. No confirmation just the text."])
def test_hello_world(hello_world_message):
    hello_world_response = "Hello, World!"
    hello_world_message = f"Please reply with just the words {hello_world_response} and nothing else. Do not run code. No confirmation just the text. This is a test."

    hello_world_message = f"Please reply with just the words {hello_world_response} and nothing else. Do not run code. No confirmation just the text."

    messages = interpreter.chat(hello_world_message)

    assert messages == [
        {"role": "user", "message": hello_world_message},
        {"role": "assistant", "message": hello_world_response},
    ]

@mark.skip(reason="Math is hard")
@mark.parametrize("min_number, max_number", [(randbelow(100), randbelow(10000))])
def test_order_of_operations(min_number, max_number):
    n1 = randbelow(max_number - min_number + 1) + min_number
    n2 = randbelow(max_number - min_number + 1) + min_number
    n2 = randint(min_number, max_number)

    test_result = n1 + n2 * (n1 - n2) / (n2 + n1)

    order_of_operations_message = f"""
    Please perform the calculation `{n1} + {n2} * ({n1} - {n2}) / ({n2} + {n1})` then reply with just the answer, nothing else. No confirmation. No explanation. No words. Do not use commas. Do not show your work. Just return the result of the calculation. Do not introduce the results with a phrase like \"The result of the calculation is...\" or \"The answer is...\"
    Round to 2 decimal places.
    """.strip()

    messages = interpreter.chat(order_of_operations_message)

    if not str(round(test_result, 2)) in messages[-1]["message"]:
        raise AssertionError()

@mark.parametrize("delayed_exec_message", ["Can you write a single block of code and run_code it that prints something, then delays 1 second, then prints something else? No talk just code. Thanks!"])
def test_delayed_exec(delayed_exec_message):
    interpreter.chat(delayed_exec_message)

@mark.skip(reason="This works fine when I run it but fails frequently in Github Actions... will look into it after the hackathon")
@mark.parametrize("nested_loops_message", ["Can you write a nested for loop in python and shell and run them? Don't forget to properly format your shell script and use semicolons where necessary. Also put 1-3 newlines between each line in the code. Only generate and execute the code. No explanations. Thanks!"])
def test_nested_loops_and_multiple_newlines(nested_loops_message):
    interpreter.chat(nested_loops_message)


@mark.parametrize("markdown_message", ["Hi, can you test out a bunch of markdown features? Try writing a fenced code block, a table, headers, everything. DO NOT write the markdown inside a markdown code block, just write it raw."])
def test_markdown(markdown_message):
    interpreter.chat(markdown_message)

from unittest.mock import patch
from subprocess import CompletedProcess
from subprocess import SubprocessError
import pytest

from home.faz.devski.open_interpreter.interpreter.core.respond import respond


def test_respond_success():
    with patch(
        "subprocess.run",
        return_value=CompletedProcess(
            args=["/usr/bin/python3", "user_program.py"],
            returncode=0,
            stdout=b"Success",
            stderr=b"",
        ),
    ):
        if respond() != "Success": raise Exception("Test failed: Expected 'Success'")


def test_respond_error():
    with patch("subprocess.run", side_effect=SubprocessError):
        if respond() is not None: raise Exception("Test failed: Expected None")

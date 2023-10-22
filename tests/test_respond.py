from unittest.mock import patch
from subprocess import CompletedProcess
import pytest

from home.faz.devski.open-interpreter.interpreter.core.respond import respond

def test_respond_success():
    with patch('subprocess.run', return_value=CompletedProcess(args=['/usr/bin/python3', 'user_program.py'], returncode=0, stdout=b'Success', stderr=b'')):
        assert respond() == 'Success'

def test_respond_error():
    with patch('subprocess.run', side_effect=SubprocessError):
        assert respond() is None

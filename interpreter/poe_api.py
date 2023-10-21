import requests


class PoeAPI:
    def __init__(self, base_url="https://api.poe.com"):
        self.base_url = base_url

    def get_endpoint(self, endpoint):
        response = requests.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()


import pytest
from unittest.mock import patch
from interpreter.poe_api import PoeAPI


@patch("requests.get")
def test_get_endpoint(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    mock_get.return_value.raise_for_status.return_value = None

    poe_api = PoeAPI()
    response = poe_api.get_endpoint("test_endpoint")

    mock_get.assert_called_once_with("https://api.poe.com/test_endpoint")
    assert_equal(response, {"data": "test"})

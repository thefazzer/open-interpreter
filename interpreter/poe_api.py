import requests
from unittest.mock import patch


class PoeAPI:
    def __init__(self, base_url="https://api.poe.com"):
        self.base_url = base_url

    def get_endpoint(self, endpoint):
        response = requests.get(f"{self.base_url}/{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()


# Moved to the top of the file


@patch("requests.get")
def test_get_endpoint(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    mock_get.return_value.raise_for_status.return_value = None

    poe_api = PoeAPI()
    response = poe_api.get_endpoint("test_endpoint")

    mock_get.assert_called_once_with("https://api.poe.com/test_endpoint")
    if response != {"data": "test"}:
        raise AssertionError("Response does not match expected value")

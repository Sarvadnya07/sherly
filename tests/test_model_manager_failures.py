import pytest
import requests
from unittest.mock import patch, MagicMock
from sherly.services.model_manager import ask_model

@patch("requests.post")
def test_ask_model_timeout_fallback(mock_post):
    # Simulate a timeout
    mock_post.side_effect = TimeoutError("LLM call exceeded 15.0s")
    
    with patch("sherly.services.model_manager.search_web") as mock_search:
        mock_search.return_value = [{"title": "Fallback", "body": "Web Result"}]
        
        # We need to mock the current model to be something that triggers a network call
        with patch("sherly.services.model_manager.get_current_model", return_value="openai"):
            with patch("sherly.services.model_manager.get_api_key", return_value="test_key"):
                result = ask_model("Tell me a joke")
                assert "Fallback. Web Result" in result

@patch("requests.post")
def test_ask_model_http_error(mock_post):
    # Simulate a 500 error
    mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    
    with patch("sherly.services.model_manager.get_current_model", return_value="openai"):
        with patch("sherly.services.model_manager.get_api_key", return_value="test_key"):
            with patch("sherly.services.model_manager.search_web", return_value=[]):
                result = ask_model("Tell me a joke")
                assert "Sorry, I ran into an error" in result

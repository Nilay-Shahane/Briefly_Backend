import pytest
from unittest.mock import patch, MagicMock
from ml.static_model import predict as predict_static
from ml.deep_model import predict as predict_deep

# --- Static Model Tests (spaCy) ---

def test_static_predict_success():
    """Test the frequency-based summarization logic."""
    text = (
        "FastAPI is a modern web framework. It is very fast and easy to use. "
        "Python developers love FastAPI for its speed and type safety."
    )
    # We expect 1 sentence back
    result = predict_static(text, num_sentences=1)
    
    assert isinstance(result, str)
    assert len(result) > 0
    assert "FastAPI" in result

def test_static_predict_too_short():
    """Test the fallback when text is empty or too short."""
    result = predict_static("   ", 1)
    assert result == "Text too short to summarize."

# --- Deep Model Tests (Transformers) ---

def test_deep_predict_lazy_loading():
    """Verify the deep model attempts to load if globals are None."""
    with patch("ml.deep_model.load") as mock_load:
        # We don't actually want to run the heavy model here, 
        # just check if it tries to load when model is None
        with patch("ml.deep_model.model", None):
            predict_deep("Some text", 50)
            mock_load.assert_called_once()

@patch("ml.deep_model.tokenizer")
@patch("ml.deep_model.model")
def test_deep_predict_mocked(mock_model, mock_tokenizer):
    """Test the processing logic of predict_deep without loading the 500MB model."""
    # 1. Setup mock tokenizer return
    mock_tokenizer.return_value = {"input_ids": "fake_tensor", "attention_mask": "fake_mask"}
    mock_tokenizer.model_max_length = 1024
    
    # 2. Setup mock model generation
    mock_model.generate.return_value = ["fake_summary_ids"]
    mock_model.device = "cpu"
    
    # 3. Setup mock decoding
    mock_tokenizer.decode.return_value = "This is a mocked summary."

    result = predict_deep("This is a long input text that needs to be summarized.", 50)
    
    assert result == "This is a mocked summary."
    mock_model.generate.assert_called_once()
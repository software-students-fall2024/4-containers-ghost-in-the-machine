import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app import convert_to_linear16, transcribe_audio, save_transcript_to_db

@pytest.fixture
def setup_audio_file():
    """Create a temporary .wav file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(b"Fake audio content")
        yield tmp_file.name
    os.remove(tmp_file.name)

def test_convert_to_linear16(setup_audio_file):
    """Test audio conversion."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        output = convert_to_linear16(setup_audio_file)
        assert "_linear16.wav" in output
        mock_run.assert_called_once()

def test_save_transcript_to_db():
    """Test saving transcript to MongoDB."""
    mock_collection = MagicMock()
    mock_collection.insert_one.return_value = MagicMock(inserted_id="12345")

    with patch("app.collection", mock_collection):
        result_id = save_transcript_to_db("Test transcript")
        assert result_id == "12345"
        mock_collection.insert_one.assert_called_once()

def test_save_transcript_to_db_error():
    """Test MongoDB insertion error."""
    mock_collection = MagicMock()

    mock_collection.insert_one.side_effect = RuntimeError("MongoDB insertion failed")

    with patch("app.collection", mock_collection):
        with pytest.raises(RuntimeError, match="MongoDB insertion failed"):
            save_transcript_to_db("Test transcript")

def test_transcribe_audio_with_real_file():
    """Test transcription with a real audio file because cannot eable speech-to-text api cuz it cost money lol."""
    audio_file = "real_speech.wav"

    assert os.path.exists(audio_file), f"Audio file {audio_file} not found. Run generate_audio.py to create it."

    transcript = transcribe_audio(audio_file)

    assert transcript is not None, "No transcription generated."
    print(f"Transcription result: {transcript}")

import pytest
from unittest.mock import patch, MagicMock
from app import create_app, connect_to_mongo


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.pymongo.MongoClient")
def test_login_post_new_user(mock_mongo, client):
    """Test login page (POST) with new user creation."""
    mock_users = mock_mongo.return_value["hellokittyai_db"]["users"]
    mock_users.find_one.return_value = None  # Simulate user not existing
    mock_users.insert_one.return_value = MagicMock(inserted_id="12345")

    response = client.post("/", data={"email": "test@example.com"})
    assert response.status_code == 200
    # Match a string unique to auth.html
    assert b"Verify Your Email" in response.data


@patch("app.pymongo.MongoClient")
@patch("app.pycai.Client")
def test_chat_with_character(mock_client, mock_mongo, client):
    """Test chat endpoint."""
    with client.session_transaction() as sess:
        sess["email"] = "test@example.com"
        sess["token"] = "mock-token"

    mock_chat = mock_client.return_value
    mock_chat.get_me.return_value = MagicMock(id="mock-id")
    mock_chat.connect.return_value.__enter__.return_value.new_chat.return_value = (
        MagicMock(chat_id="mock-chat-id"),
        None,
    )
    # Ensure `text` returns a plain string
    mock_message = MagicMock()
    mock_message.name = "Kitty"
    mock_message.text = "Hello, how can I help you?"
    mock_chat.send_message.return_value = mock_message

    mock_users = mock_mongo.return_value["hellokittyai_db"]["users"]

    response = client.post("/chat", json={"message": "Hi Kitty!"})
    assert response.status_code == 200
    assert b"Hello, how can I help you?" in response.data


@patch("app.pymongo.MongoClient")
def test_connect_to_mongo_failure(mock_mongo):
    """Test failed MongoDB connection."""
    # Simulate connection failure
    mock_mongo.side_effect = Exception("Connection failed")
    
    from app import connect_to_mongo
    with pytest.raises(RuntimeError, match="MongoDB connection failed."):
        connect_to_mongo("mock-uri")


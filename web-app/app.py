"""
Flask app for Hello Kitty AI application.
Handles user authentication, connection to MongoDB, and basic routes.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from characterai import pycai, sendCode, authUser
import pymongo
from bson import ObjectId
import certifi
from pydub import AudioSegment

# Configure pydub to use ffmpeg
AudioSegment.converter = "/usr/local/bin/ffmpeg"
AudioSegment.ffprobe = "/usr/local/bin/ffprobe"


def setup_logging():
    """Set up application-wide logging."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def connect_to_mongo(mongo_uri):
    """Establish a MongoDB connection."""
    mongo_client = pymongo.MongoClient(mongo_uri, tlsCAFile=certifi.where())
    try:
        mongo_client.admin.command("ping")
        logging.info("Successfully connected to MongoDB!")
        return mongo_client
    except pymongo.errors.PyMongoError as error:
        logging.error("Failed to connect to MongoDB: %s", error)
        raise RuntimeError("MongoDB connection failed.") from error


def initialize_upload_folder():
    """Initialize the upload folder."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


def load_environment_variables():
    """Load and validate required environment variables."""
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY is missing. Add it to your .env file.")

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI is missing. Add it to your .env file.")

    ml_client_url = os.getenv("ML_CLIENT_URL")
    if not ml_client_url:
        raise ValueError("ML_CLIENT_URL is missing in the .env file.")

    return secret_key, mongo_uri, ml_client_url


def create_app():
    """Creates and configures the Flask application."""
    load_dotenv()

    # Load environment variables
    secret_key, mongo_uri, _ = load_environment_variables()

    # Initialize Flask app
    flask_app = initialize_flask(secret_key)

    # Set up MongoDB
    users = setup_mongo(mongo_uri)

    # Configure routes
    configure_routes(flask_app, users)

    return flask_app


def initialize_flask(secret_key):
    """Initialize and configure the Flask app."""
    flask_app = Flask(__name__)
    flask_app.secret_key = secret_key
    flask_app.config["UPLOAD_FOLDER"] = initialize_upload_folder()
    flask_app.config["SESSION_COOKIE_HTTPONLY"] = True
    flask_app.config["SESSION_COOKIE_SECURE"] = True
    setup_logging()
    return flask_app


def setup_mongo(mongo_uri):
    """Set up MongoDB client and users collection."""
    mongo_client = connect_to_mongo(mongo_uri)
    db = mongo_client["hellokittyai_db"]
    users = db["users"]
    return users


def configure_routes(flask_app, users):
    """Define and register all routes."""
    configure_login_routes(flask_app, users)
    configure_chat_routes(flask_app, users)
    configure_audio_routes(flask_app)


def configure_login_routes(flask_app, users):
    """Define routes related to user login."""
    @flask_app.route("/", methods=["GET", "POST"])
    def login():
        """Handles user login and code sending."""
        if request.method == "POST":
            email = request.form.get("email")
            if not email:
                return "Email address is required", 400

            session["email"] = email
            user = users.find_one({"email": email})
            if not user:
                user_id = str(ObjectId())
                users.insert_one(
                    {"user_id": user_id, "email": email, "chat_history": [], "audio_analysis": []}
                )
                logging.info("New user created: %s", email)

            session["code"] = sendCode(email)
            return render_template("auth.html", address=email)

        return render_template("index.html")

    @flask_app.route("/authenticate", methods=["POST"])
    def auth():
        """Authenticates the user using the link provided."""
        link = request.form.get("link")
        if not link:
            return "Authentication link is required", 400

        email = session.get("email")
        code = session.get("code")
        if not email or not code:
            return "Session expired. Please log in again.", 403

        try:
            logging.info("Authenticating user %s", email)
            token = authUser(link, email)
            session["token"] = token
            return redirect(url_for("chat_with_character"))
        except pymongo.errors.PyMongoError as mongo_error:
            logging.error("MongoDB error: %s", mongo_error)
            return jsonify({"error": "Database error"}), 500


def configure_chat_routes(flask_app, users):
    """Define routes related to chat functionality."""
    @flask_app.route("/chat", methods=["GET", "POST"])
    def chat_with_character():
        """Handles chatting with a specific character."""
        character_id = "7xhfgdiu2oj2NIRnQQRx42Q2cwr0sFIRu7xZeRZYWn0"

        if request.method == "GET":
            return render_template("chat.html")

        token = session.get("token")
        email = session.get("email")
        if not token or not email:
            return jsonify({"error": "Client is not authenticated. Please log in."}), 403

        try:
            client = pycai.Client(token)
            me = client.get_me()

            with client.connect() as chat:
                new, _ = chat.new_chat(character_id, me.id)
                user_message = request.json.get("message")
                if not user_message:
                    return jsonify({"error": "No message provided"}), 400

                response = chat.send_message(character_id, new.chat_id, user_message)

                users.update_one(
                    {"email": email},
                    {
                        "$push": {
                            "chat_history": {
                                "timestamp": datetime.utcnow(),
                                "message": user_message,
                                "response": response.text,
                            }
                        }
                    },
                )
                logging.info("Chat saved for %s: %s -> %s", email, user_message, response.text)
                return jsonify(
                    {"character_name": response.name, "character_message": response.text}
                )
        except pymongo.errors.PyMongoError as mongo_error:
            logging.error("MongoDB error: %s", mongo_error)
            return jsonify({"error": "Database error"}), 500


def configure_audio_routes(flask_app):
    """Define routes related to audio functionality."""
    @flask_app.route("/convert-to-wav", methods=["POST"])
    def convert_to_wav():
        """Converts uploaded audio to WAV format."""
        if "audio" not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400

        audio_file = request.files["audio"]
        original_filename = secure_filename(audio_file.filename)
        original_file_path = os.path.join(flask_app.config["UPLOAD_FOLDER"], original_filename)

        try:
            audio_file.save(original_file_path)
            audio = AudioSegment.from_file(original_file_path)
            wav_file_path = os.path.splitext(original_file_path)[0] + ".wav"
            audio.export(
                wav_file_path,
                format="wav",
                parameters=["-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1"]
            )
            logging.info("File successfully converted to WAV: %s", wav_file_path)
            return jsonify({"message": "Converted to WAV", "wav_file_path": wav_file_path}), 200
        except FileNotFoundError as file_error:
            logging.error("File not found: %s", file_error)
            return jsonify({"error": "File not found"}), 500

if __name__ == "__main__":
    app_instance = create_app()
    app_instance.run(host="0.0.0.0", port=8000)

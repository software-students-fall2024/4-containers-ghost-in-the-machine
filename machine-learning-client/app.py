"""
Machine Learning Client for Hello Kitty AI application.
Monitors a shared folder for audio files, processes them, and stores transcriptions in MongoDB.
"""

import os
import logging
import subprocess
import time
import re
import certifi
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pymongo import MongoClient, errors
from google.cloud import speech
from google.api_core.exceptions import GoogleAPICallError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("pymongo").setLevel(logging.WARNING)

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI is missing. Add it to your .env file.")

try:
    logging.info("Connecting to MongoDB with URI: %s", mongo_uri)
    mongo_client = MongoClient(
        mongo_uri,
        tlsCAFile=certifi.where()
    )
    db = mongo_client["hellokittyai_db"]
    collection = db["speech_data"]
    mongo_client.admin.command("ping")
    logging.info("Successfully connected to MongoDB!")
except errors.PyMongoError as error:
    logging.error("Failed to connect to MongoDB: %s", error)
    raise RuntimeError("MongoDB connection failed.") from error

# Path to the shared uploads folder in the `web-app`
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../web-app/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Google Speech-to-Text client
try:
    speech_client = speech.SpeechClient()
    logging.info("Google Speech-to-Text client initialized.")
except Exception as error:
    logging.error("Failed to initialize Speech-to-Text client: %s", error)
    raise RuntimeError("Speech-to-Text client initialization failed.") from error

# Track processed files to avoid duplicate processing
processed_files = set()

def convert_to_linear16(filepath):
    """Convert the audio file to LINEAR16 format."""
    logging.debug("Converting %s to LINEAR16 format...", filepath)
    output_path = filepath.replace(".wav", "_linear16.wav")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                filepath,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                output_path,
            ],
            check=True,  # Explicitly define 'check'
        )
        logging.debug("Conversion successful: %s", output_path)
        return output_path
    except subprocess.CalledProcessError as error:
        logging.error("FFmpeg conversion failed for %s: %s", filepath, error)
        raise RuntimeError(f"FFmpeg conversion failed: {error}") from error

def transcribe_audio(filepath):
    """Transcribe audio using Google Speech-to-Text API."""
    logging.debug("Transcribing audio: %s", filepath)
    try:
        with open(filepath, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = speech_client.recognize(config=config, audio=audio)
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            logging.debug("Transcription successful: %s", transcript)
            return transcript
        logging.warning("No speech recognized in audio: %s", filepath)
        return None
    except GoogleAPICallError as error:
        logging.error("Speech-to-Text API error for %s: %s", filepath, error)
        raise RuntimeError(f"Speech-to-Text API error: {error}") from error


def save_transcript_to_db(transcript):
    """Save the transcript to the MongoDB database."""
    logging.debug("Saving transcript to MongoDB: %s", transcript)
    try:
        result = collection.insert_one({"transcript": transcript})
        logging.info("Transcript saved with ID: %s", result.inserted_id)
        return str(result.inserted_id)
    except errors.PyMongoError as error:
        logging.error("MongoDB insertion failed: %s", error)
        raise RuntimeError(f"MongoDB insertion failed: {error}") from error


def cleanup_files(*files):
    """Delete temporary files."""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                logging.info("Deleted file: %s", file)
        except OSError as error:
            logging.error("Failed to delete file %s: %s", file, error)


def process_file(filepath):
    """Process a single audio file."""
    if filepath in processed_files:
        logging.info("File already processed (in process_file), skipping: %s", filepath)
        return

    logging.info("Processing file: %s", filepath)
    try:
        processed_files.add(filepath)
        converted_filepath = convert_to_linear16(filepath)
        transcript = transcribe_audio(converted_filepath)

        if transcript:
            save_transcript_to_db(transcript)
            logging.info("File processed and transcript saved: %s", filepath)
        else:
            logging.warning("No transcription generated for file: %s", filepath)
    except RuntimeError as error:
        logging.error("Error processing file %s: %s", filepath, error)
    finally:
        logging.info("Calling cleanup_files for %s", filepath)
        cleanup_files(filepath, filepath.replace(".wav", "_linear16.wav"))


class AudioFileHandler(FileSystemEventHandler):
    """Handles new files in the uploads folder."""

    def on_created(self, event):
        """Handle created events."""
        if not event.is_directory and event.src_path.endswith(".wav"):
            logging.info("New file detected: %s", event.src_path)
            self.schedule_processing(event.src_path)

    def on_modified(self, event):
        """Handle modified events."""
        if not event.is_directory and event.src_path.endswith(".wav"):
            logging.info("File modified: %s", event.src_path)
            self.schedule_processing(event.src_path)

    def schedule_processing(self, filepath):
        """
        Schedule processing for the file after ensuring it is stable.
        Files are processed only if the size remains unchanged for 2 seconds.
        """
        if filepath in processed_files:
            logging.debug("File already processed (in schedule_processing), skipping: %s", filepath)
            return

        if re.search(r"_linear16\.wav$", filepath):
            logging.debug("Ignoring intermediate file: %s", filepath)
            return

        def process_if_stable():
            time.sleep(2)
            if not os.path.exists(filepath):
                return

            current_size = os.path.getsize(filepath)
            time.sleep(1)
            if not os.path.exists(filepath):
                return

            final_size = os.path.getsize(filepath)
            if current_size == final_size:
                logging.info("File is stable, processing: %s", filepath)
                process_file(filepath)
            else:
                logging.debug("File size still changing, re-checking: %s", filepath)
                self.schedule_processing(filepath)

        Thread(target=process_if_stable).start()


if __name__ == "__main__":
    observer = Observer()
    event_handler = AudioFileHandler()
    observer.schedule(event_handler, UPLOAD_FOLDER, recursive=False)
    observer.start()

    try:
        logging.info("Machine-learning-client is monitoring the uploads folder...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


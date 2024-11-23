"""
File for generating a basic audio file.
"""
import subprocess
from gtts import gTTS

def main():
    """Generate a basic audio file with speech and convert it to LINEAR16."""
    text = "This is a test audio file generated for the speech recognition system."
    output_file = "real_speech_temp.wav"
    final_file = "real_speech.wav"

    print("Generating a test audio file with speech using gTTS...")
    tts = gTTS(text=text, lang="en")
    tts.save(output_file)

    print("Converting audio to LINEAR16 format...")
    subprocess.run(
        ["ffmpeg", "-i", output_file, "-ar", "16000", "-ac", "1", final_file],
        check=True
    )
    print(f"Audio file converted and saved as: {final_file}")

if __name__ == "__main__":
    main()
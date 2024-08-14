import os
from google.cloud import speech
from google.cloud import storage
import time 

def find_mp3_file(directory: str) -> str:
    """Finds the only MP3 file in the given directory."""
    mp3_files = [file for file in os.listdir(directory) if file.endswith('.mp3')]
    if len(mp3_files) != 1:
        raise ValueError(f"Expected exactly one MP3 file in the directory, but found {len(mp3_files)}.")
    return mp3_files[0]

def upload_to_gcs(bucket_name: str, source_file_name: str, destination_blob_name: str) -> str:
    """Uploads a file to the Google Cloud Storage bucket."""
    storage_client = storage.Client.from_service_account_json("duke-432500-b9356f938653.json")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    return f"gs://{bucket_name}/{destination_blob_name}"

def google_speech_transcribe_gcs(gcs_uri: str, language_code="en-US") -> str:
    """Transcribes an audio file from Google Cloud Storage using the Batch Recognize method."""
    client = speech.SpeechClient.from_service_account_json("duke-432500-b9356f938653.json")

    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        language_code=language_code,
        sample_rate_hertz=16000,  # Ensure this matches the sample rate of the audio file
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,  # Use MP3 encoding for MP3 files
        enable_automatic_punctuation=True  # Optional: Enables automatic punctuation
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    print("Waiting for operation to complete...")

    minutes = 0
    while not operation.done():
        print(f"Operation not completed yet. Waiting for another 60 seconds (minutes elapsed: {minutes}).")
        time.sleep(60)  # Wait for 60 seconds before polling again
        minutes+=1

    response = operation.result()

    transcription = ""
    for result in response.results:
        transcription += result.alternatives[0].transcript + "\n"

    return transcription


# Example usage
directory = "."  # Current directory
bucket_name = "y1s1-lectures"  # Replace with your GCS bucket name

# Find the MP3 file in the directory
source_file_name = find_mp3_file(directory)
destination_blob_name = f"audio/{source_file_name}"  # Destination path in GCS

# Upload the audio file to GCS
gcs_uri = upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
print(f"File uploaded to {gcs_uri}")

# Transcribe the audio file
transcription = google_speech_transcribe_gcs(gcs_uri)
print("Transcription:", transcription)

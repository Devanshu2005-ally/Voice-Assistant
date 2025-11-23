from resemblyzer import VoiceEncoder, preprocess_wav
import sounddevice as sd
import noisereduce as nr
import librosa
from numpy.linalg import norm
import soundfile as sf
from pathlib import Path
import numpy as np
import io
import os
from database import User, get_db_session # Import for DB interaction
import sys

# Ensure the Voice Encoder is loaded at startup
try:
    _encoder = VoiceEncoder()
except Exception as e:
    print(f"❌ ERROR: Failed to load Resemblyzer VoiceEncoder. Check dependencies like 'numpy', 'librosa', and 'scipy'. Error: {e}")
    # Exit registration script gracefully if encoder fails
    sys.exit(1)


def serialize_embedding(embedding):
    """Converts a numpy array (embedding) to a binary format for database storage."""
    # Use io.BytesIO to simulate a file and numpy.save to write binary data
    with io.BytesIO() as f:
        np.save(f, embedding)
        return f.getvalue()

def amplify_audio(audio, target_peak=0.8):
        current_peak = np.max(np.abs(audio)) + 1e-8
        gain = target_peak / current_peak
        amplified = audio * gain
        amplified = np.clip(amplified, -1.0, 1.0)
        return amplified


def registeration():
    fs = 16000
    duration = 7
    encoder = _encoder # Use the globally loaded encoder
    embeddings = [] # List to collect all 3 embeddings
    
    temp_files = [] # To clean up temporary audio files
    user_id = "user" # Hardcoded for demo consistency

    for i in range(1, 4):  # exactly 3 samples
        raw_filename = f"temp_raw_{user_id}_{i}.wav"
        cleaned_filename = f"temp_cleaned_{user_id}_{i}.wav"
        temp_files.extend([raw_filename, cleaned_filename])
        
        try:
            # --- Recording ---
            print(f"\n🎤 Recording sample {i}/3 ({duration} seconds)... Speak now!")
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float64')
            sd.wait()  # Wait until recording is finished
            
            # Save raw recording
            sf.write(raw_filename, recording, fs)
            
            # --- Preprocessing ---
            # 1. Noise Reduction
            # Convert to float32 as expected by noisereduce
            audio_np = recording.flatten().astype(np.float32)
            reduced_noise = nr.reduce_noise(y=audio_np, sr=fs, prop_decrease=0.8, n_fft=512)
            
            # 2. Amplify
            amplified = amplify_audio(reduced_noise, target_peak=0.9)

            sf.write(cleaned_filename, amplified, fs)
            print(f"✨ Cleaned audio saved temporarily: {cleaned_filename}")

            # Generating and collecting the embedding
            # preprocess_wav expects 16kHz audio
            wav = preprocess_wav(Path(cleaned_filename)) 
            embedding = encoder.embed_utterance(wav)
            embeddings.append(embedding)
            print(f"📌 Embedding generated for sample {i}")
            
        except Exception as e:
            print(f"\n❌ ERROR during recording/processing sample {i}: {e}")
            print("Ensure your microphone is connected and system permissions are granted.")
            # Clear all temporary files and exit on failure
            for f in temp_files:
                if os.path.exists(f): os.remove(f)
            sys.exit(1)

        
    # --- DB Storage Logic ---
    
    if embeddings:
        # Calculate the mean embedding from the 3 samples
        mean_embedding = np.mean(embeddings, axis=0)
        
        # Normalize the final embedding
        mean_embedding = mean_embedding / norm(mean_embedding)
        
        # Serialize the numpy array
        db_embedding = serialize_embedding(mean_embedding)

        # Store in DB
        db = get_db_session()
        # Use DB ID 1, consistent with main.py's demo mapping
        db_id = 1 
        user = db.query(User).filter(User.id == db_id).first() 

        if user:
            user.voice_embedding = db_embedding
            db.commit()
            print(f"\n✅ Mean embedding stored in the database for User ID {db_id}.")
        else:
            print(f"\n❌ Error: User ID {db_id} not found in database. Run 'python main.py' once to initialize the DB.")
        
        db.close()
        
    # --- Cleanup ---
    for f in temp_files:
        if os.path.exists(f): 
            try:
                os.remove(f)
            except Exception as e:
                print(f"Warning: Could not remove temporary file {f}. {e}")
    print("\nCleanup complete.")


if __name__ == "__main__":
    # Initialize the DB just in case it wasn't run by main.py
    from database import init_db
    init_db()
    registeration()
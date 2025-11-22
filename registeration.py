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


def registeration(user_id):
    fs = 16000
    duration = 7
    encoder = VoiceEncoder()
    embeddings = [] # List to collect all 3 embeddings
    
    temp_files = [] # To clean up temporary audio files

    for i in range(1, 4):  # exactly 3 samples
        print(f"\n🎤 Recording sample {i}/3... Speak now!")

        # File names for this sample
        raw_filename = f"temp_{user_id}_raw_{i}.wav"
        cleaned_filename = f"temp_{user_id}_cleaned_{i}.wav"
        temp_files.extend([raw_filename, cleaned_filename])

        # Recording
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        sf.write(raw_filename, audio, fs)
        print(f"📁 Raw audio saved temporarily: {raw_filename}")

        # Cleaning
        audio_np, sr = librosa.load(raw_filename, sr=16000)
        audio_np = audio_np / (np.max(np.abs(audio_np)) + 1e-8)

        # Noise reduction
        noise_sample = audio_np[:4000] if len(audio_np) > 4000 else audio_np
        denoised = nr.reduce_noise(y=audio_np, y_noise=noise_sample, sr=sr, prop_decrease=0.9)
        amplified = amplify_audio(denoised, target_peak=0.9)

        sf.write(cleaned_filename, amplified, sr)
        print(f"✨ Cleaned audio saved temporarily: {cleaned_filename}")

        # Generating and collecting the embedding
        wav = preprocess_wav(Path(cleaned_filename))
        embedding = encoder.embed_utterance(wav)
        embeddings.append(embedding)
        print(f"📌 Embedding generated for sample {i}")
        
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
            print(f"\n❌ Error: User ID {db_id} not found in database.")
        
        db.close()
        
    # --- Final Cleanup ---
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
    print("🧹 Temporary audio files cleaned up.")


registeration('user')
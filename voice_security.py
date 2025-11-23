# voice_security.py
import io
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from numpy.linalg import norm
import noisereduce as nr
import librosa
import soundfile as sf
from pathlib import Path
from database import User, get_db_session # Import User model and session helper
import os


def deserialize_embedding(binary_data):
    """Converts binary data from the database back to a numpy array (embedding)."""
    if not binary_data: return None
    with io.BytesIO(binary_data) as f:
        # numpy.load expects a file-like object
        return np.load(f)

class VoiceSecurity:
    def __init__(self):
        print("Loading Voice Encoder...")
        try:
            self.encoder = VoiceEncoder()
            self.loaded = True
            print("✅ Voice Encoder Ready")
        except Exception as e:
            print(f"❌ ERROR: Failed to load Resemblyzer VoiceEncoder. Voice verification disabled. Error: {e}")
            self.encoder = None
            self.loaded = False

    def amplify_audio(self, audio, target_peak=0.9):
        current_peak = np.max(np.abs(audio)) + 1e-8
        gain = target_peak / current_peak
        amplified = audio * gain
        return np.clip(amplified, -1.0, 1.0)

    def clean_audio(self, file_path):
        # Load audio at 16k sample rate
        audio_np, sr = librosa.load(file_path, sr=16000)
        
        # Normalize
        audio_np = audio_np / (np.max(np.abs(audio_np)) + 1e-8)
        
        # Noise Reduction
        reduced_noise = nr.reduce_noise(y=audio_np, sr=sr, prop_decrease=0.8, n_fft=512)
        
        # Amplify
        cleaned_audio = self.amplify_audio(reduced_noise)
        
        # Save to a temporary file path required by preprocess_wav
        temp_cleaned_path = f"{file_path}_cleaned.wav"
        sf.write(temp_cleaned_path, cleaned_audio, sr)
        
        return temp_cleaned_path

    def verify_user(self, input_audio_path: str, user_id: str, threshold=0.75):
        if not self.loaded:
            return False, 0.0, "Voice Encoder not loaded. Verification disabled."
            
        # Mapping "user" string to DB ID 1 for demo consistency with main.py
        db_id = 1
        
        db = get_db_session()
        user = db.query(User).filter(User.id == db_id).first()
        
        if not user:
            db.close()
            return False, 0.0, f"Error: User ID {db_id} not found in database."
        
        # 1. Retrieve embedding from DB and deserialize
        binary_embed = user.voice_embedding
        db.close()
        
        if not binary_embed:
            return False, 0.0, "No reference voice embedding found in database. Run 'python registeration.py'."
            
        mean_embed = deserialize_embedding(binary_embed)
        # Normalize the mean embedding retrieved from DB
        mean_embed = mean_embed / norm(mean_embed)

        cleaned_audio_path = None
        try:
            # 2. Preprocess the incoming audio
            cleaned_audio_path = self.clean_audio(input_audio_path)
            wav = preprocess_wav(Path(cleaned_audio_path))
            embedding_new = self.encoder.embed_utterance(wav)
            embedding_new = embedding_new / norm(embedding_new)

            # 3. Compute Cosine Similarity
            score = np.dot(mean_embed, embedding_new)
            
            is_verified = score >= threshold
            return is_verified, float(score), "Access Granted" if is_verified else "Voice Mismatch"

        except Exception as e:
            print(f"Error during voice verification process: {e}")
            return False, 0.0, f"Processing Error: {e}"
        finally:
            # Cleanup the temporary cleaned audio file
            if cleaned_audio_path and os.path.exists(cleaned_audio_path):
                os.remove(cleaned_audio_path)

# Instantiate the Voice Security class
voice_guard = VoiceSecurity()
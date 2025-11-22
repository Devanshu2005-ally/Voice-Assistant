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

def deserialize_embedding(binary_data):
    """Converts binary data from the database back to a numpy array (embedding)."""
    if not binary_data: return None
    with io.BytesIO(binary_data) as f:
        # numpy.load expects a file-like object
        return np.load(f)

class VoiceSecurity:
    def __init__(self):
        print("Loading Voice Encoder...")
        self.encoder = VoiceEncoder()

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
        
        # Reduce Noise
        if len(audio_np) > 4000:
            noise_sample = audio_np[:4000]
            cleaned = nr.reduce_noise(y=audio_np, y_noise=noise_sample, sr=sr, prop_decrease=0.8)
        else:
            cleaned = audio_np # Audio too short to profile noise
            
        return self.amplify_audio(cleaned)

    def verify_user(self, input_audio_path, user_id, threshold=0.75):
        """
        Returns (is_verified: bool, score: float, message: str)
        """
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
            return False, 0.0, "No reference voice embedding found in database."
            
        mean_embed = deserialize_embedding(binary_embed)
        # Normalize the mean embedding retrieved from DB
        mean_embed = mean_embed / norm(mean_embed)

        try:
            # 2. Preprocess the incoming audio
            cleaned_audio = self.clean_audio(input_audio_path)
            wav = preprocess_wav(cleaned_audio)
            embedding_new = self.encoder.embed_utterance(wav)
            embedding_new = embedding_new / norm(embedding_new)

            # 3. Compute Cosine Similarity
            score = np.dot(mean_embed, embedding_new)
            
            is_verified = score >= threshold
            return is_verified, float(score), "Access Granted" if is_verified else "Voice Mismatch"

        except Exception as e:
            return False, 0.0, f"Error during verification: {str(e)}"

# Singleton instance
voice_guard = VoiceSecurity()
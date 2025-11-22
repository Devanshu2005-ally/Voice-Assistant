from resemblyzer import VoiceEncoder, preprocess_wav
import sounddevice as sd
from scipy.io.wavfile import write
import noisereduce as nr
import librosa
from numpy.linalg import norm
import soundfile as sf
from pathlib import Path
import numpy as np
import io
import sys
import whisper
from googletrans import Translator
from feature import sent2features
import pickle
import joblib
from check_balance import tell_balance
from gtts import gTTS
from pydub import AudioSegment
import simpleaudio as sa
from io import BytesIO
# From route import route_to_api





#verification step

fs = 16000
duration = 7  # fallback if silence not detected
threshold = 0.80  # similarity threshold
print("🎤 Speak now for authentication...")

encoder = VoiceEncoder()

#recording new audio
audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
sd.wait()


#convert to BytesIO for processing
buffer = io.BytesIO()
sf.write(buffer, audio, fs, format='wav')
buffer.seek(0)

audio_np, sr = sf.read(buffer, dtype='float32')  # audio_np: float32 array, sr: sample rate
audio_np = audio_np / (np.max(np.abs(audio_np)) + 1e-8)
# use first 0.25 seconds as noise
noise_sample = audio_np[:4000]
cleaned = nr.reduce_noise(y=audio_np, y_noise=noise_sample, sr=sr, prop_decrease=0.9)

def amplify_audio(audio, target_peak=0.8):
    current_peak = np.max(np.abs(audio)) + 1e-8
    gain = target_peak / current_peak
    amplified = audio * gain
    amplified = np.clip(amplified, -1.0, 1.0)
    return amplified

amplified = amplify_audio(cleaned, target_peak=0.9)

sf.write("new_cleaned.wav", amplified, sr)

if audio_np.ndim > 1:
    audio_np = audio_np.mean(axis=1)  # convert to mono if stereo

if sr != 16000:
    audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)
    sr = 16000


#preprocess and embed
wav = preprocess_wav(audio_np)
embedding_new = encoder.embed_utterance(wav)

#load reference embedding
e1 = np.load("1_embedding.npy")
e2 = np.load("2_embedding.npy")
e3 = np.load("3_embedding.npy")

e1 = e1 / norm(e1)
e2 = e2 / norm(e2)
e3 = e3 / norm(e3)

mean_embed = np.mean([e1, e2, e3], axis=0)

mean_embed = mean_embed / norm(mean_embed)

embedding_new = embedding_new / norm(embedding_new)

#compute cosine similarity
sim = np.dot(mean_embed, embedding_new)
print(f"Similarity Score: {sim:.2f}")
#load the models




#checking similarity against threshold
if sim >= threshold:
    print(f"🔍 Similarity Score: {sim:.2f}")

    print("✅ Verification successful")
    

else:
    sys.exit("❌ Verification failed. Voice did not matched.")



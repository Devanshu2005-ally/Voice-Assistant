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



def amplify_audio(audio, target_peak=0.8):
        current_peak = np.max(np.abs(audio)) + 1e-8
        gain = target_peak / current_peak
        amplified = audio * gain
        amplified = np.clip(amplified, -1.0, 1.0)
        return amplified


def registeration(user):
    fs = 16000
    duration = 7
    encoder = VoiceEncoder()

    for i in range(1, 4):  # exactly 3 samples
        print(f"\n🎤 Recording sample {i}/3... Speak now!")

        # File names for this sample
        raw_filename = f"{user}_voice_{i}.wav"
        cleaned_filename = f"{user}_cleaned_{i}.wav"
        embedding_filename = f"{user}_embedding_{i}.npy"

        # Recording
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        sf.write(raw_filename, audio, fs)
        print(f"📁 Raw audio saved: {raw_filename}")

        # Cleaning
        audio_np, sr = librosa.load(raw_filename, sr=16000)
        audio_np = audio_np / (np.max(np.abs(audio_np)) + 1e-8)

        noise_sample = audio_np[:4000]
        denoised = nr.reduce_noise(y=audio_np, y_noise=noise_sample, sr=sr, prop_decrease=0.9)
        amplified = amplify_audio(denoised, target_peak=0.9)

        sf.write(cleaned_filename, amplified, sr)
        print(f"✨ Cleaned audio saved: {cleaned_filename}")

        #Storing the embedding
        wav = preprocess_wav(Path(cleaned_filename))
        embedding = encoder.embed_utterance(wav)

        np.save(embedding_filename, embedding)
        print(f"📌 Embedding saved: {embedding_filename}  | shape={embedding.shape}")


registeration('user')
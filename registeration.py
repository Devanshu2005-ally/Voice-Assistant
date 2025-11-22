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



def registeration(filename, cleaned_filename, embedding_filename):
    fs = 16000
    duration = 7

    print("🎤 Recording... Speak now!")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished

    # Step 2: Save as a WAV file
    write(filename, fs, audio)
    print("✅ Recording complete")

    #cleaning of voice 
    audio, sr = librosa.load(filename, sr=16000)
    audio = audio / (np.max(np.abs(audio)) + 1e-8)
    noise_sample = audio[:4000]   # use first 0.25 seconds as noise

    cleaned = nr.reduce_noise(y=audio, y_noise=noise_sample, sr=sr, prop_decrease=0.9)

    def amplify_audio(audio, target_peak=0.8):
        current_peak = np.max(np.abs(audio)) + 1e-8
        gain = target_peak / current_peak
        amplified = audio * gain
        amplified = np.clip(amplified, -1.0, 1.0)
        return amplified

    amplified = amplify_audio(cleaned, target_peak=0.9)

    sf.write(cleaned_filename, amplified, sr)

    # loading the audio file
    wav_path = Path(cleaned_filename)
    wav = preprocess_wav(wav_path)

    # creating the encoder
    encoder = VoiceEncoder()

    # generating the embedding
    embed = encoder.embed_utterance(wav)
    print("✅ Voice embedding generated.")
    print("Voice embedding shape:", embed.shape)

    np.save(embedding_filename, embed)

registeration("2_voice.wav", "2_cleaned.wav", "2_embedding.npy")

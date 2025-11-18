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

model = joblib.load("intent_model.pkl")
tfidf = joblib.load("tfidf_vectorizer.pkl")

with open("slot_filling_crf_model.pkl", "rb") as f:
    crf = pickle.load(f)


def predict_intent(text):
    vect = tfidf.transform([text])
    intent = model.predict(vect)[0]
    return intent

def predict_slots(text):
    sentence_tokens = text.split()
    features = sent2features([(t, 'O') for t in sentence_tokens])
    pred = crf.predict([features])[0]
    return list(zip(sentence_tokens, pred))


def extract_slot_dict(token_label_pairs):
    slots = {}
    current_slot = None
    current_tokens = []

    for token, label in token_label_pairs:
        if label.startswith("B-"):
            # Save previous slot if exists
            if current_slot is not None:
                slots[current_slot] = " ".join(current_tokens)

            # Start new slot
            current_slot = label[2:]  # remove "B-"
            current_tokens = [token]

        elif label.startswith("I-") and current_slot == label[2:]:
            current_tokens.append(token)

        else:
            # Close slot if active
            if current_slot is not None:
                slots[current_slot] = " ".join(current_tokens)
                current_slot = None
                current_tokens = []

    # Add last slot
    if current_slot is not None:
        slots[current_slot] = " ".join(current_tokens)

    return slots


def transcribe_and_translate():
    model = whisper.load_model("base")
    result = model.transcribe("new_cleaned.wav", task = 'translate')
    text = result["text"]
    detected_lang = result["language"]
    print(f"Detected language: {detected_lang}")
    print(f"Original text: {text}")
    intent = predict_intent(text)
    slot_pairs = predict_slots(text)
    slots = extract_slot_dict(slot_pairs)
    print(f"Predicted Intent: {intent}")
    print(f"Extracted Slots: {slots}")
    return intent, slots


#checking similarity against threshold
if sim >= threshold:
    print(f"🔍 Similarity Score: {sim:.2f}")

    print("✅ Verification successful")
<<<<<<< HEAD
    intent, slots = transcribe_and_translate()
=======
    transcribe_and_translate()
>>>>>>> 920fe1c175e442c78850fa681d6afa47cadd6858

else:
    sys.exit("❌ Verification failed. Voice did not matched.")


def predict_sub_intent(text):
    text = text.lower()

    if "eligibility" in text or "eligible" in text:
        return "loan_eligibility"
    if "apply" in text or "application" in text:
        return "loan_apply"
    if "status" in text or "track" in text:
        return "loan_status"
    
    if "document" in text or "docs" in text:
        return "loan_documents"
    if "interest rate" in text or "rate" in text or "emi" in text:
        return "loan_interest_rate"

    return "general_query"

<<<<<<< HEAD
def predict_credit_sub_intent(text):
    text = text.lower()
    
    # Check available credit limit
    if "available" in text or "remaining" in text or "left" in text or "credit limit" in text:
        return "credit_limit_available"

    # Check used/consumed credit limit
    if "used" in text or "utilized" in text or "consumed" in text or "spend" in text:
        return "credit_limit_used"

    # Check eligibility for credit card
    if "eligibility" in text or "eligible" in text:
        return "credit_eligibility"

    # Check for credit limit increase
    if "increase" in text or "raise" in text or "higher" in text:
        return "credit_limit_increase"
    # Default fallback
    return "credit_general_query"
=======

>>>>>>> 920fe1c175e442c78850fa681d6afa47cadd6858


def dialog_manager(intent, slots):
    """
    Dialog Manager:
    - Checks for required slots
    - If missing, asks user via speech
    - If complete, calls the API and returns response
    """
    # Define required slots for each intent
    REQUIRED_SLOTS = {
<<<<<<< HEAD
        "transfer": ["amount", "recipient", "account_number"],
        "check_balance": [],
        "check_transactions": ["start_date", "end_date"]
=======
        "transfer": ["amount", "recipient"],
        "check_balance": [],
        "check_transactions": ["date_range"],
>>>>>>> 920fe1c175e442c78850fa681d6afa47cadd6858

        #for loan inquiry intent
        "loan types": [],
        "loan_interest_rate": ["loan_type"],
        "loan_eligibility": ["loan_type", "income", "credit_score"],
        "loan_status": ["user_id"],
        "loan_required_documents": ["loan_type"],
        "loan_processing_time": ["loan_type"],
<<<<<<< HEAD


        #for credit card intent
        "credit_check": ["card_type", "card_name"],
        "credit_limit_available": ["card_type", "card_name"],
        "credit_limit_used": ["card_type", "card_name"],
        "credit_limit_increase": ["card_type", "card_name", "requested_increase_amount"],
        "credit_eligibility": ["card_type", "income", "credit_score"]
        
    }
    if intent == "loan_inquiry":
        sub_intent = predict_loan_sub_intent(user_text)

        

        # All loan slots present → API call
        response = route_to_api(sub_intent, slots)
        return {
            "status": "complete",
            "intent": sub_intent,
            "slots": slots,
            "api_response": response
        }
    
    
    
    if intent == "credit_limit":
        sub_intent = predict_credit_sub_intent(user_text)

        

        # All credit card slots present → API call
        response = route_to_api(sub_intent, slots)
        return {
            "status": "complete",
            "intent": sub_intent,
            "slots": slots,
            "api_response": response
        }
    
    
    
    
    # Check for missing slots
    
=======
        
    }

    # Check for missing slots
    missing = [s for s in REQUIRED_SLOTS.get(intent, []) if s not in slots or not slots[s]]

    if missing:
        # Ask for the first missing slot
        slot_to_ask = missing[0]
        message = f"Please tell me the {slot_to_ask}."
        print(message)
        speak(message)
        return {
            "status": "missing_info",
            "missing_slot": slot_to_ask,
            "message": message
        }
>>>>>>> 920fe1c175e442c78850fa681d6afa47cadd6858

    # If all slots are present → call API
    response = route_to_api(intent, slots)
    
    # Speak out the result
    

    return {
        "status": "complete",
<<<<<<< HEAD
        "intent": intent,
        "slots": slots,
        "api_response": response,
        
    }

slot_dict = dialog_manager(intent, slots)

sent = slot_dict['api_response']

def speak(text):
    # Generate speech in memory
    mp3_fp = BytesIO()
    tts = gTTS(text=sent, lang='en')
    tts.write_to_fp(mp3_fp)

    # Load into pydub without saving
    mp3_fp.seek(0)
    audio = AudioSegment.from_file(mp3_fp, format="mp3")

    # Play audio
    play_obj = sa.play_buffer(
        audio.raw_data,
        num_channels=audio.channels,
        bytes_per_sample=audio.sample_width,
        sample_rate=audio.frame_rate
    )
    play_obj.wait_done()
=======
        "slots": slots,
        "api_response": response,
        "message": message
    }

# def speak(text):
#     # Generate speech in memory
#     mp3_fp = BytesIO()
#     tts = gTTS(text=sent, lang='en')
#     tts.write_to_fp(mp3_fp)

#     # Load into pydub without saving
#     mp3_fp.seek(0)
#     audio = AudioSegment.from_file(mp3_fp, format="mp3")

#     # Play audio
#     play_obj = sa.play_buffer(
#         audio.raw_data,
#         num_channels=audio.channels,
#         bytes_per_sample=audio.sample_width,
#         sample_rate=audio.frame_rate
#     )
#     play_obj.wait_done()
>>>>>>> 920fe1c175e442c78850fa681d6afa47cadd6858





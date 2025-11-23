import joblib
import pickle
import numpy as np
from feature import sent2features
from googletrans import Translator
import os
import nltk

# Ensure necessary NLTK data is downloaded
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("⏳ Downloading NLTK resources...")
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt')
    print("✅ NLTK resources downloaded.")


class MLEngine:
    def __init__(self):
        print("⏳ Loading ML Models...")
        self.intent_model = None
        self.tfidf = None
        self.crf = None
        self.translator = Translator()
        
        # Load Intent Model
        if os.path.exists("intent_model.pkl") and os.path.exists("tfidf_vectorizer.pkl"):
            try:
                self.intent_model = joblib.load("intent_model.pkl")
                self.tfidf = joblib.load("tfidf_vectorizer.pkl")
            except Exception as e:
                 print(f"❌ Error loading Intent Model: {e}. Run 'python intent_model.py' to generate.")
        else:
            print("⚠️ Intent Model files (intent_model.pkl/tfidf_vectorizer.pkl) not found. Intent prediction disabled.")
        
        # Load Slot Filling Model
        if os.path.exists("slot_filling_crf_model.pkl"):
            try:
                with open("slot_filling_crf_model.pkl", "rb") as f:
                    self.crf = pickle.load(f)
            except Exception as e:
                 print(f"❌ Error loading Slot Filling Model: {e}. Run 'python slotfill.py' to generate.")
        else:
            print("⚠️ Slot Filling Model (slot_filling_crf_model.pkl) not found. Slot prediction disabled.")

        print("✅ Models loading sequence complete.")

    def predict_intent(self, text):
        if not self.intent_model: return "general_query"
        vect = self.tfidf.transform([text])
        return self.intent_model.predict(vect)[0]

    def predict_slots(self, text):
        if not self.crf: return {}
        
        # Tokenize and Tag: NLTK POS tagging is necessary to generate features expected by the CRF model.
        sentence_tokens = nltk.word_tokenize(text)
        
        try:
            # sentence_tagged is a list of (word, postag) tuples
            sentence_tagged = nltk.pos_tag(sentence_tokens)
        except LookupError:
             # Fallback if resources fail. This is rare if the check in __init__ is successful.
             sentence_tagged = [(w, 'NN') for w in sentence_tokens]

        # sent2features expects (word, postag) which sentence_tagged provides.
        features = sent2features(sentence_tagged)
        
        try:
            # The CRF model predicts a list of labels (e.g., ['O', 'B-amount', 'I-amount', 'O'])
            pred = self.crf.predict([features])[0]
        except IndexError:
            return {}
        
        # Extract slots (I-O-B format)
        slots = {}
        current_slot = None
        current_vals = []
        
        for token, label in zip(sentence_tokens, pred):
            if label.startswith("B-"):
                if current_slot: slots[current_slot] = " ".join(current_vals)
                current_slot = label[2:]
                current_vals = [token]
            elif label.startswith("I-") and current_slot == label[2:]:
                current_vals.append(token)
            else:
                if current_slot: slots[current_slot] = " ".join(current_vals)
                current_slot = None
                current_vals = []
        
        if current_slot: slots[current_slot] = " ".join(current_vals)
        return slots

    def predict_sub_intent(self, text):
        text = text.lower()
        if "status" in text: return "loan_status"
        if "eligib" in text: return "loan_eligibility"
        if "interest" in text or "rate" in text: return "loan_interest_rate"
        return "general_loan_query"

    def predict_credit_sub_intent(self, text):
        text = text.lower()
        if "available" in text or "left" in text: return "available_limit"
        if "used" in text or "spent" in text: return "used_limit"
        return "general_credit_query"

# Instantiate the ML Engine globally
ml_engine = MLEngine()
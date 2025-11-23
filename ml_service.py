import joblib
import pickle
import numpy as np
from token_feature import sent2features
from googletrans import Translator
import os





class MLEngine:
    def __init__(self):
        print("⏳ Loading ML Models...")
        self.intent_model = None
        self.tfidf = None
        self.crf = None
        self.translator = Translator()
        
        # Load Intent Model
        if os.path.exists("intent_model.pkl") and os.path.exists("tfidf_vectorizer.pkl"):
            self.intent_model = joblib.load("intent_model.pkl")
            self.tfidf = joblib.load("tfidf_vectorizer.pkl")
        
        # Load Slot Filling Model
        if os.path.exists("slot_filling_crf_model.pkl"):
            with open("slot_filling_crf_model.pkl", "rb") as f:
                self.crf = pickle.load(f)

        print("✅ Models loading sequence complete.")

    def predict_intent(self, text):
        if not self.intent_model: return "general_query"
        vect = self.tfidf.transform([text])
        return self.intent_model.predict(vect)[0]
        
    def predict_slots(self, text):
        if not self.crf: return {}
        
        tokens = text.split()
        
        # FIX: Generate REAL POS tags using NLTK
        # The feature.py expects tuple (word, postag)
        
        
        features = sent2features([(t, 'O') for t in tokens])
        
        try:
            pred = self.crf.predict([features])[0]
        except IndexError:
            return {}
        
        # Extract slots
        slots = {}
        current_slot = None
        current_vals = []
        
        for token, label in zip(tokens, pred):
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
        if "available" in text or "balance" in text: return "credit_limit_available"
        if "used" in text or "due" in text: return "credit_limit_used"
        return "general_credit_query"

ml_engine = MLEngine()


from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import shutil
import os
import whisper 
import soundfile as sf
import numpy as np

import database
# UPDATED: Import Transaction model
from database import User, Account, Loan, CreditCard, Transaction, get_db 
import ml_service
from voice_security import voice_guard # Import our new security class


database.init_db()

app = FastAPI(title="Voice Banking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model for STT
print("⏳ Loading Whisper Model...")
# NOTE: Ensure you have the 'base' whisper model installed or change to 'tiny' for speed
try:
    whisper_model = whisper.load_model("base") 
    print("✅ Whisper Ready")
except Exception as e:
    print(f"❌ Whisper Model Load Failed. Ensure 'ffmpeg' is installed and PATH is set. Error: {e}")
    whisper_model = None

# Initialize Voice Security
voice_guard = voice_guard() 

class ChatRequest(BaseModel):
    message: str
    language: str = "en-US"
    user_id: str = "user" # Changed to String to match filenames

class ChatResponse(BaseModel):
    response: str
    is_verified: bool = True
    transcription: str | None = None


def route_to_db(intent, slots, sub_intent, user_id, db: Session):
    # Mapping "user" string to ID 1 for DB demo
    db_id = 1 
    user = db.query(User).filter(User.id == db_id).first() 
    
    if not user:
        return "I could not find your user profile in the database."

    # --- Intent Handling ---
    if intent == "check_balance":
        account = db.query(Account).filter(Account.user_id == db_id).first()
        if account:
            return f"Your current account balance is ₹{account.balance:,.2f}."
        else:
            return "I couldn't retrieve your account balance."

    elif intent == "transaction_history":
        # Logic to fetch and summarize last few transactions
        transactions = db.query(Transaction).filter(Transaction.user_id == db_id).order_by(Transaction.transaction_date.desc()).limit(3).all()
        if transactions:
            history = [f"{t.transaction_date}: {t.description} ({t.amount:.2f})" for t in transactions]
            return "Here are your last 3 transactions:\n" + "\n".join(history)
        else:
            return "No recent transactions found."

    elif intent == "loan_inquiry":
        loan = db.query(Loan).filter(Loan.user_id == db_id).first()
        if sub_intent == "loan_status":
             return f"Your {loan.loan_type} status is currently '{loan.status}'. The amount is ₹{loan.amount:,.0f}."
        elif sub_intent == "loan_eligibility":
            return "Based on your current profile, you are pre-approved for a Personal Loan up to ₹5,00,000."
        elif sub_intent == "loan_interest_rate":
            return "Our current Home Loan interest rate is 8.5% p.a."
        else:
            return "I can check your loan status, eligibility, or current interest rates. Which one are you interested in?"

    elif intent == "credit_limit":
        card = db.query(CreditCard).filter(CreditCard.user_id == db_id).first()
        if card:
            if sub_intent == "available_limit":
                available = card.limit_available - card.limit_used
                return f"Your available credit limit on your {card.card_name} is ₹{available:,.2f}."
            elif sub_intent == "used_limit":
                return f"Your used credit limit on your {card.card_name} is ₹{card.limit_used:,.2f}."
            else:
                return f"Your total credit limit is ₹{card.limit_available:,.0f}. Used: ₹{card.limit_used:,.0f}. Available: ₹{card.limit_available - card.limit_used:,.0f}."
        else:
            return "I couldn't find your credit card details."

    elif intent == "transfer":
        # Example Slot-Filling Logic
        amount = slots.get('amount')
        recipient = slots.get('recipient')
        
        if amount and recipient:
            # Simulate a transfer
            amount_val = float(amount.replace('₹', '').replace(',', '').replace('INR', '').replace('rupees', '').strip())
            
            # Simple check if balance is sufficient
            account = db.query(Account).filter(Account.user_id == db_id).first()
            if account.balance >= amount_val:
                # Update DB (Simulation)
                account.balance -= amount_val
                db.add(Transaction(user_id=db_id, transaction_date="TODAY", description=f"Transfer to {recipient}", amount=-amount_val))
                db.commit()
                return f"Transfer successful. ₹{amount_val:,.2f} sent to {recipient}. Your new balance is ₹{account.balance:,.2f}."
            else:
                return "Transfer failed: Insufficient balance."
        else:
            return "To complete the transfer, please specify the amount and the recipient."

    elif intent == "general_query":
        return "I processed your request, but I currently only support banking queries like checking balance, transfers, loans, and credit cards. Please try rephrasing."

    else:
        # Catch-all fallback
        return "I processed your request but need more training data to handle this specific intent. Please try another banking query."


def process_request(text, language, user_id, db):
    # Logic shared between text and voice
    
    # Translation (Hindi -> En)
    if language == 'hi-IN':
        try:
            translation = ml_service.ml_engine.translator.translate(text, src='hi', dest='en')
            text = translation.text
        except: pass

    # ML
    intent = ml_service.ml_engine.predict_intent(text)
    # The slots dictionary is critical for extracting the amount and recipient for the transfer
    slots = ml_service.ml_engine.predict_slots(text) 
    
    sub_intent = None
    if intent == "loan_inquiry": sub_intent = ml_service.ml_engine.predict_sub_intent(text)
    elif intent == "credit_limit": sub_intent = ml_service.ml_engine.predict_credit_sub_intent(text)

    # DB
    response_text = route_to_db(intent, slots, sub_intent, user_id, db)

    # Translation (En -> Hindi)
    if language == 'hi-IN':
        try:
            translation = ml_service.ml_engine.translator.translate(response_text, src='en', dest='hi')
            response_text = translation.text
        except: pass
        
    return response_text


@app.post("/chat/", response_model=ChatResponse)
def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    print(f"Text Input: {request.message} (Lang: {request.language})")
    response_text = process_request(request.message, request.language, request.user_id, db)
    return ChatResponse(response=response_text)


@app.post("/voice-chat/", response_model=ChatResponse)
async def handle_voice_chat(
    audio_file: UploadFile = File(...),
    language: str = Form("en-US"),
    user_id: str = Form("user"),
    db: Session = Depends(get_db)
):
    if not whisper_model:
        raise HTTPException(status_code=500, detail="Whisper model not loaded. Check server logs.")

    temp_filename = f"temp_audio_{user_id}.wav"
    
    # Save the uploaded file temporarily
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # --- 1. VOICE SECURITY CHECK ---
        is_verified, score, security_response = voice_guard.verify_user(temp_filename, user_id)
        print(f"Voice Verification Score: {score:.2f}, Result: {security_response}")

        if not is_verified:
            # Security failed: Return immediate error response
            return ChatResponse(
                response=f"Security Alert: Voice verification failed. Score: {score:.2f}. Please try again.",
                is_verified=False,
                transcription="Security check required."
            )

        # --- 2. SPEECH-TO-TEXT (STT) ---
        # Whisper expects a path or a NumPy array. Load with soundfile for Whisper's internal processing.
        audio_np, _ = sf.read(temp_filename, dtype='float32')
        result = whisper_model.transcribe(audio_np, language="en" if language == 'en-US' else 'hi')
        transcription = result["text"].strip()

        print(f"Transcription: {transcription} (Lang: {language})")

        if not transcription:
             return ChatResponse(response="I couldn't understand the audio. Please speak clearly.", is_verified=True, transcription="")

        # --- 3. ML/DB Processing ---
        response_text = process_request(transcription, language, user_id, db)
        
        return ChatResponse(response=response_text, is_verified=True, transcription=transcription)

    except Exception as e:
        print(f"An error occurred during voice chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
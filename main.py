from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import shutil
import os
import whisper 

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
whisper_model = whisper.load_model("base") 
print("✅ Whisper Ready")

class ChatRequest(BaseModel):
    message: str
    language: str = "en-US"
    user_id: str = "user" # Changed to String to match filenames

def route_to_db(intent, slots, sub_intent, user_id, db: Session):
    # Mapping "user" string to ID 1 for DB demo
    db_id = 1 
    user = db.query(User).filter(User.id == db_id).first()
    
    if intent == "check_balance":
        acc = db.query(Account).filter(Account.user_id == db_id).first()
        return f"Your balance is ₹{acc.balance:,.2f}." if acc else "No account."

    # NEW: Money Transfer/Payment Logic
    if intent == "make_payment":
        try:
            # Assumes ML service correctly extracted the 'amount' slot
            amount_str = slots.get('amount')
            
            # Simple check for required slot
            if not amount_str:
                return "Please specify the amount you wish to transfer."
            
            # Clean and convert the slot value to float
            # Note: This simple cleaning assumes the amount is the only thing in the slot
            amount = float(amount_str.replace('₹', '').replace(',', '').strip())
            
            acc = db.query(Account).filter(Account.user_id == db_id).first()
            if not acc: return "No account found to process payment."
            
            if acc.balance >= amount:
                acc.balance -= amount # Debit the user's account
                
                # Log the transaction
                db.add(Transaction(user_id=db_id, transaction_date="2025-11-23", 
                                   description=f"Fund Transfer to {slots.get('recipient', 'External Account')}", 
                                   amount=amount, transaction_type="Debit"))
                
                db.commit()
                # In a real system, you would credit a recipient account here.
                return f"Successfully transferred ₹{amount:,.2f}. Your new balance is ₹{acc.balance:,.2f}."
            else:
                return f"Insufficient balance. Your current balance is only ₹{acc.balance:,.2f}."
                
        except ValueError:
            return "I could not understand the transfer amount. Please provide a valid number."
        except Exception as e:
            print(f"Payment error: {e}")
            return "An unexpected error occurred while trying to process the payment."

    if intent == "loan_inquiry":
        if sub_intent == "loan_status":
            loans = db.query(Loan).filter(Loan.user_id == db_id).all()
            if loans: return f"Your {loans[0].loan_type} status is: {loans[0].status}."
            return "No active loans."
        return "You are eligible for a Personal Loan."

    if intent == "credit_limit":
        card = db.query(CreditCard).filter(CreditCard.user_id == db_id).first()
        if not card: return "No credit card found."
        if sub_intent == "credit_limit_used": return f"Used limit: ₹{card.limit_used:,.2f}"
        return f"Available limit: ₹{card.limit_available:,.2f}"

    # NEW: Transaction History Logic
    if intent == "transaction_history":
        # Fetch the last 3 transactions for the user
        transactions = db.query(Transaction).filter(Transaction.user_id == db_id).order_by(Transaction.id.desc()).limit(3).all()
        
        if not transactions:
            return "I couldn't find any recent transactions for your account."
            
        summary = ["Your three most recent transactions are:"]
        for t in transactions:
            # Format the output for natural conversation
            summary.append(f"On {t.transaction_date}, a {t.transaction_type} of ₹{t.amount:,.2f} for {t.description}.")
            
        return "\n".join(summary)


    return "I processed your request but need more training on this specific topic."

@app.post("/chat")
async def text_chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Standard Text Chat (No Voice Security Check)"""
    return process_request(request.message, request.language, request.user_id, db)

@app.post("/voice-chat")
async def voice_chat_endpoint(
    audio: UploadFile = File(...),
    language: str = Form("en-US"),
    user_id: str = Form("user"),
    db: Session = Depends(get_db)
):
    """Voice Endpoint: Verifies Biometrics first, then processes intent"""
    
    # 1. Save temporary audio file
    temp_filename = f"temp_{user_id}.wav"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    try:
        # 2. VOICE SECURITY CHECK
        print(f"🔐 Verifying voice for {user_id}...")
        is_verified, score, msg = voice_guard.verify_user(temp_filename, user_id)
        print(f"   ↳ Result: {msg} (Score: {score:.2f})")

        if not is_verified:
            return {"response": f"Security Alert: Voice verification failed. (Score: {score:.2f})", "verified": False}

        # 3. Speech to Text (Transcribe) using Whisper
        result = whisper_model.transcribe(temp_filename)
        transcribed_text = result["text"]
        print(f"🗣️ Transcribed: {transcribed_text}")

        # 4. Process Intent
        response_data = process_request(transcribed_text, language, user_id, db)
        response_data["verified"] = True
        return response_data

    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

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
        
    return {
        "response": response_text,
        "transcription": text,
        "intent": intent,
        "slots": slots # Added slots to the response
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
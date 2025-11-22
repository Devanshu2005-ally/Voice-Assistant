from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database
from database import User, Account, Loan, CreditCard, get_db
import ml_service

# Initialize DB on startup
database.init_db()

# --- FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Voice Banking API")

# Allow CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Input Schema ---
class ChatRequest(BaseModel):
    message: str
    language: str = "en-US"
    user_id: int = 1  # Hardcoded user ID for demonstration

# --- Logic Router ---
def route_to_db(intent, slots, sub_intent, user_id, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "User not found."

    # --- Intents ---
    if intent == "check_balance":
        acc = db.query(Account).filter(Account.user_id == user_id).first()
        if acc:
            return f"Your current account balance is ₹{acc.balance:,.2f}."
        return "No account found for this user."

    if intent == "loan_inquiry":
        if sub_intent == "loan_status":
            loans = db.query(Loan).filter(Loan.user_id == user_id).all()
            if not loans: return "You have no active loans in the system."
            loan = loans[0] # Taking the first loan for simplicity
            return f"The status of your {loan.loan_type} for ₹{loan.amount:,.0f} is currently **{loan.status}**."
        
        if sub_intent == "loan_eligibility":
            return "Based on our records, you are pre-approved for a Personal Loan up to ₹10 Lakhs at 10% interest."
        
        if sub_intent == "loan_interest_rate":
             loan_type = slots.get('loan_type', 'Personal Loan')
             return f"The current interest rate for a {loan_type} is 9.5% per annum."

    if intent == "credit_limit":
        card = db.query(CreditCard).filter(CreditCard.user_id == user_id).first()
        if not card: return "No credit card found for this user."
        
        if sub_intent == "credit_limit_available":
            return f"Your available limit on the **{card.card_name}** is ₹{card.limit_available:,.2f}."
        
        if sub_intent == "credit_limit_used":
            return f"You have utilized ₹{card.limit_used:,.2f} of your credit limit."
            
    # Default fallback
    return f"I detected the intent: {intent}. I am still learning how to handle that specific request."

# --- Endpoints ---

@app.get("/")
def root():
    return {"status": "Banking Assistant API is Online", "ML_Status": "Ready"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    text = request.message
    print(f"📩 Received: {text} | Lang: {request.language}")

    # 1. Translation: Hindi -> English (if needed)
    if request.language == 'hi-IN':
        try:
            # Note: In a heavy production app, run this in a threadpool
            translation = ml_service.ml_engine.translator.translate(text, src='hi', dest='en')
            text = translation.text
            print(f"   ↳ Translated to: {text}")
        except Exception as e:
            print(f"   ❌ Translation Error: {e}")

    # 2. ML Processing
    intent = ml_service.ml_engine.predict_intent(text)
    slots = ml_service.ml_engine.predict_slots(text)
    
    # Determine Sub-intents based on context
    sub_intent = None
    if intent == "loan_inquiry":
        sub_intent = ml_service.ml_engine.predict_sub_intent(text)
    elif intent == "credit_limit":
        sub_intent = ml_service.ml_engine.predict_credit_sub_intent(text)

    # 3. Database Routing
    response_text = route_to_db(intent, slots, sub_intent, request.user_id, db)

    # 4. Translation: English -> Hindi (if needed)
    if request.language == 'hi-IN':
        try:
            translation = ml_service.ml_engine.translator.translate(response_text, src='en', dest='hi')
            response_text = translation.text
        except Exception as e:
            print(f"   ❌ Response Translation Error: {e}")
            
    print(f"📢 Responding: {response_text}")

    return {
        "response": response_text,
        "intent": intent,
        "slots": slots
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
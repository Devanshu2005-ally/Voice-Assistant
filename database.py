from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel

# --- 1. DATABASE CONFIGURATION ---
DATABASE_URL = "sqlite:///./banking_assistant.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DATABASE MODELS (Tables) ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    # Storing the voice embedding (numpy array) as binary data
    voice_embedding = Column(LargeBinary, nullable=True) 
    
    # Relationships
    accounts = relationship("Account", back_populates="owner")
    loans = relationship("Loan", back_populates="owner")
    credit_cards = relationship("CreditCard", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_number = Column(String, unique=True, index=True)
    balance = Column(Float, default=0.0)
    
    owner = relationship("User", back_populates="accounts")

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    loan_type = Column(String)  # e.g., "Home", "Personal"
    status = Column(String)    # e.g., "Approved", "Pending"
    amount = Column(Float)
    
    owner = relationship("User", back_populates="loans")

class CreditCard(Base):
    __tablename__ = "credit_cards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_name = Column(String)          # e.g., "Platinum Rewards"
    limit_available = Column(Float)
    limit_used = Column(Float)
    
    owner = relationship("User", back_populates="credit_cards")

# --- 3. PYDANTIC SCHEMAS (For API validation) ---
class AccountUpdate(BaseModel):
    amount: float

class UserResponse(BaseModel):
    name: str
    
    class Config:
        from_attributes = True

# --- 4. INITIALIZE EXAMPLE DATA ---
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if data exists, if not, add dummy data
    if not db.query(User).first():
        print("⚡ Populating DB with dummy data...")
        
        # Create User
        user = User(name="Amit Sharma")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create Account
        db.add(Account(user_id=user.id, account_number="1234567890", balance=50000.0))
        
        # Create Loan
        db.add(Loan(user_id=user.id, loan_type="Home Loan", status="Approved", amount=2500000.0))
        
        # Create Credit Card
        db.add(CreditCard(user_id=user.id, card_name="HDFC Regalia", limit_available=80000.0, limit_used=20000.0))
        
        db.commit()
        print("✅ Example data loaded.")
    
    db.close()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
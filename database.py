from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel
from sqlalchemy.orm import Session # Added for type hinting

# --- 1. DATABASE CONFIGURATION ---
DATABASE_URL = "sqlite:///./banking_assistant.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session (for FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper to get a standalone DB session (for scripts like registration/security)
def get_db_session() -> Session:
    """Returns a standalone database session for scripts (not FastAPI dependencies)."""
    db = SessionLocal()
    return db

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
    transactions = relationship("Transaction", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_number = Column(String, unique=True, index=True)
    balance = Column(Float)
    
    owner = relationship("User", back_populates="accounts")

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    loan_type = Column(String)
    status = Column(String) # E.g., Approved, Pending, Rejected
    amount = Column(Float)
    
    owner = relationship("User", back_populates="loans")

class CreditCard(Base):
    __tablename__ = "credit_cards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_name = Column(String)
    limit_available = Column(Float)
    limit_used = Column(Float)
    
    owner = relationship("User", back_populates="credit_cards")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_date = Column(String) # Keeping as string for simplicity in demo
    description = Column(String)
    amount = Column(Float)
    
    owner = relationship("User", back_populates="transactions")

# --- 3. Pydantic Schemas (for FastAPI request/response) ---
class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    voice_embedding: bytes | None
    
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
        # Initial balance set to 50,000
        db.add(Account(user_id=user.id, account_number="1234567890", balance=50000.0))
        
        # Create Loan
        db.add(Loan(user_id=user.id, loan_type="Home Loan", status="Approved", amount=2500000.0))
        
        # Create Credit Card
        db.add(CreditCard(user_id=user.id, card_name="HDFC Regalia", limit_available=80000.0, limit_used=20000.0))
        
        # ADDED: Example Transactions for User ID 1
        db.add(Transaction(user_id=user.id, transaction_date="2025-11-20", description="Online Purchase - Amazon", amount=1500.00))
        db.add(Transaction(user_id=user.id, transaction_date="2025-11-21", description="ATM Withdrawal", amount=5000.00))
        db.add(Transaction(user_id=user.id, transaction_date="2025-11-22", description="Salary Deposit", amount=45000.00))

        db.commit()
        print("✅ DB populated with dummy data for User ID 1.")
    
    db.close()
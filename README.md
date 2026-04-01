🗣️ AI Voice Assistant for Financial Operations
📖 Project Overview
In today’s digital banking world, customers expect seamless, personalized, and hands-free experiences. Yet, many users—especially those less familiar with complex applications—struggle with basic tasks like checking balances, transferring funds, or making loan inquiries.

The Challenge: Design an AI-powered Voice Banking Assistant that enables users to perform secure financial operations through natural conversation.

The Solution:
This project delivers a highly accessible, convenient, and fast voice assistant. It understands natural language, responds intelligently, and executes actions safely, all while ensuring strict compliance and privacy standards.

✨ Key Features
Hands-Free Banking: Perform core banking tasks (balance checks, fund transfers, loan inquiries) entirely via voice commands.

High-Accuracy Speech Processing: Utilizes transfer learning with the Whisper model for robust Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities.

Intelligent Natural Language Understanding (NLU):

Intent Recognition: Accurately determines what the user wants to do (e.g., "Send money" vs. "Check balance").

Slot Filling: Extracts critical entities from the conversation (e.g., Amount, Payee Name, Account Type).

Lightning Fast Backend: Powered by FastAPI for asynchronous, high-performance API routing.

Secure & Compliant: Designed with financial safety and privacy in mind, securely handling data before executing database transactions.

🛠️ Technology Stack
Frontend:

HTML5, CSS3, Vanilla JavaScript (Web Speech API integration & UI)

Backend:

Python & FastAPI (main.py)

Database Management: SQLite/PostgreSQL handled via database.py

Machine Learning & AI:

Voice Processing: Whisper Model (Transfer Learning for STT/TTS)

Intent Classification: Custom ML model (intent.py)

Entity Extraction: Custom slot-filling model (slotfill.py)

📂 Project Structure
Plaintext
📦 AI-Voice-Banking-Assistant
 ┣ 📂 frontend
 ┃ ┣ 📜 index.html          # Chat/Voice interface
 ┃ ┣ 📜 styles.css          # UI styling
 ┃ ┗ 📜 app.js              # Audio capture and API calls
 ┣ 📂 backend
 ┃ ┣ 📜 main.py             # FastAPI entry point and route definitions
 ┃ ┣ 📜 intent.py           # ML model for Intent Classification
 ┃ ┣ 📜 slotfill.py         # ML model for Slot Filling/Entity Extraction
 ┃ ┗ 📜 database.py         # DB connection, CRUD operations, and transaction logic
 ┣ 📜 requirements.txt      # Python dependencies
 ┗ 📜 README.md             # Project documentation
🚀 Installation & Setup
Prerequisites
Python 3.8+

Node.js/Live Server (Optional, for serving the frontend)

FFmpeg (Required for Whisper audio processing)

1. Clone the Repository
Bash
git clone [https://github.com/yourusername/AI-Voice-Banking-Assistant.git](https://github.com/yourusername/AI-Voice-Banking-Assistant.git)
cd AI-Voice-Banking-Assistant
2. Set Up the Backend Environment
Create and activate a virtual environment:

Bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
3. Install Dependencies
Bash
pip install -r requirements.txt
4. Run the Backend Server
Start the FastAPI server using Uvicorn:

Bash
uvicorn backend.main:app --reload
The API will be available at http://localhost:8000. You can view the interactive API documentation at http://localhost:8000/docs.

5. Run the Frontend
Simply open frontend/index.html in your browser, or use a live server extension in your IDE (like VS Code) to serve the static files.

🧠 How the AI Pipeline Works
Audio Capture: The user clicks the microphone button on the frontend (HTML/JS) and speaks a command.

Speech-to-Text (STT): The audio blob is sent to main.py and processed by the Whisper model to generate highly accurate text.

Intent Classification: The text string is passed to intent.py, which identifies the user's goal (e.g., TRANSFER_FUNDS).

Slot Filling: slotfill.py parses the text to extract the required parameters (e.g., {amount: 500, currency: "dollars", payee: "John"}).

Execution: database.py verifies the account balance and executes the transaction securely.

Text-to-Speech (TTS): A success message is generated, converted back into audio, and played for the user on the frontend.

🔒 Security & Privacy
Data Minimization: Audio files are processed in-memory and deleted immediately after transcription.

Transaction Verification: All high-risk operations (like fund transfers) require explicit verbal or UI confirmation before database.py commits the transaction.

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.
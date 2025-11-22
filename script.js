document.addEventListener("DOMContentLoaded", function() {

    // --- UI Elements ---
    const assistantIcon = document.getElementById('assistant-icon');
    const chatBox = document.getElementById('chat-assistant-box');
    const closeChatButton = document.getElementById('close-chat');
    const languageSelector = document.getElementById('language-selector');
    
    const chatTitle = document.getElementById('chat-title');
    const chatInput = document.getElementById('chat-input');
    const chatStatus = document.getElementById('chat-status');
    const chatBody = document.getElementById('chat-body');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('start-voice-btn');

    // --- Translation Dictionary ---
    const translations = {
        'en-US': {
            title: "Virtual Assistant",
            placeholder: "Type your message...",
            listening: "Listening...",
            processing: "Thinking...",
            error: "Error detected.",
            noVoice: "Voice input not supported.",
            welcome: "Hello! How can I help you with your banking today?",
            botPrefix: "Bot: "
        },
        'hi-IN': {
            title: "आभासी सहायक", // Virtual Assistant
            placeholder: "अपना संदेश लिखें...", // Type your message
            listening: "सुन रहा हूँ...",
            processing: "सोच रहा हूँ...",
            error: "त्रुटि पाई गई।", // Error
            noVoice: "आवाज़ इनपुट समर्थित नहीं है।", 
            welcome: "नमस्ते! मैं आपकी बैंकिंग में कैसे मदद कर सकता हूँ?",
            botPrefix: "बॉट: "
        }
    };

    // Current Language State (Default English)
    let currentLang = 'en-US';

    // --- Toggle Chatbox ---
    function toggleChatbox() {
        chatBox.classList.toggle('show');
        // Auto-focus input when opened
        if (chatBox.classList.contains('show')) {
            setTimeout(() => chatInput.focus(), 300);
        }
    }
    if(assistantIcon) assistantIcon.addEventListener('click', toggleChatbox);
    if(closeChatButton) closeChatButton.addEventListener('click', toggleChatbox);

    // --- Language Switching Logic ---
    if(languageSelector) {
        languageSelector.addEventListener('change', (e) => {
            currentLang = e.target.value;
            updateInterfaceLanguage(currentLang);
        });
    }

    function updateInterfaceLanguage(lang) {
        const t = translations[lang];
        
        if(chatTitle) chatTitle.textContent = t.title;
        if(chatInput) chatInput.placeholder = t.placeholder;
        
        // Add a system message indicating language switch
        addMessageToChat(lang === 'hi-IN' ? "भाषा हिंदी में बदल दी गई है।" : "Language switched to English.", 'bot');
    }

    // --- Voice Assistant Logic ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition && voiceBtn) {
        const recognition = new SpeechRecognition();
        recognition.interimResults = false;

        voiceBtn.addEventListener('click', () => {
            recognition.lang = currentLang; 
            try {
                recognition.start();
            } catch (error) {
                console.error("Recognition already started or error:", error);
            }
        });

        recognition.onstart = () => {
            if(chatStatus) chatStatus.textContent = translations[currentLang].listening;
            voiceBtn.classList.add('listening');
        };

        recognition.onend = () => {
            voiceBtn.classList.remove('listening');
            // Status cleared in sendTranscript
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            addMessageToChat(transcript, 'user');
            sendTranscriptToModel(transcript, currentLang);
        };

        recognition.onerror = (event) => {
            console.error("Speech Error:", event.error);
            if(chatStatus) chatStatus.textContent = translations[currentLang].error;
            voiceBtn.classList.remove('listening');
        };

    } else if (voiceBtn) {
        console.error("Speech Recognition not supported.");
        if(chatStatus) chatStatus.textContent = translations[currentLang].noVoice;
        voiceBtn.style.display = "none";
    }

    // --- Sending Messages ---
    if(sendBtn) {
        sendBtn.addEventListener('click', () => {
            const text = chatInput.value.trim();
            if (text) {
                addMessageToChat(text, 'user');
                sendTranscriptToModel(text, currentLang);
                chatInput.value = '';
            }
        });
    }

    if(chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendBtn.click();
        });
    }

    function addMessageToChat(message, sender) {
        const p = document.createElement('p');
        p.textContent = message;
        p.className = (sender === 'user') ? 'user-message' : 'bot-message';
        chatBody.appendChild(p);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // --- API Connection ---
    async function sendTranscriptToModel(transcript, lang) {
        console.log(`Sending to Backend [Lang: ${lang}]:`, transcript);
        
        if(chatStatus) chatStatus.textContent = translations[lang].processing; 

        try {
            const response = await fetch('http://127.0.0.1:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: transcript,
                    language: lang,
                    user_id: 1 // Hardcoded user ID for demonstration
                })
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();
            
            // Add the bot's response to the chat
            addMessageToChat(data.response, 'bot');
            
        } catch (error) {
            console.error("Connection Error:", error);
            const errorMessage = lang === 'en-US' 
                ? "Could not connect to the banking server." 
                : "बैंकिंग सर्वर से संपर्क नहीं हो सका।";
            addMessageToChat(errorMessage, 'bot');
        } finally {
            if(chatStatus) chatStatus.textContent = ""; 
        }
    }
});

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
            error: "Error detected.",
            noVoice: "Voice input not supported.",
            welcome: "Hello! How can I help you today?",
            botPrefix: "You said: "
        },
        'hi-IN': {
            title: "आभासी सहायक", // Virtual Assistant
            placeholder: "अपना संदेश लिखें...", // Type your message
            listening: "सुन रहा हूँ...", // Listening
            error: "त्रुटि पाई गई।", // Error
            noVoice: "आवाज़ इनपुट समर्थित नहीं है।", 
            welcome: "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?",
            botPrefix: "आपने कहा: "
        }
    };

    // Current Language State (Default English)
    let currentLang = 'en-US';

    // --- Toggle Chatbox ---
    function toggleChatbox() {
        chatBox.classList.toggle('show');
    }
    assistantIcon.addEventListener('click', toggleChatbox);
    closeChatButton.addEventListener('click', toggleChatbox);

    // --- Language Switching Logic ---
    languageSelector.addEventListener('change', (e) => {
        currentLang = e.target.value;
        updateInterfaceLanguage(currentLang);
    });

    function updateInterfaceLanguage(lang) {
        const t = translations[lang];
        
        // Update Static Text
        chatTitle.textContent = t.title;
        chatInput.placeholder = t.placeholder;
        
        // Add a system message indicating language switch
        addMessageToChat(lang === 'hi-IN' ? "भाषा हिंदी में बदल दी गई है।" : "Language switched to English.", 'bot');
    }

    // --- Voice Assistant Logic ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.interimResults = false;

        voiceBtn.addEventListener('click', () => {
            // IMPORTANT: Set the recognition language based on the dropdown selection
            recognition.lang = currentLang; 
            try {
                recognition.start();
            } catch (error) {
                console.error("Recognition already started.", error);
            }
        });

        recognition.onstart = () => {
            chatStatus.textContent = translations[currentLang].listening;
            voiceBtn.classList.add('listening');
        };

        recognition.onend = () => {
            chatStatus.textContent = ""; 
            voiceBtn.classList.remove('listening');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            addMessageToChat(transcript, 'user');
            sendTranscriptToModel(transcript, currentLang);
        };

        recognition.onerror = (event) => {
            console.error("Speech Error:", event.error);
            chatStatus.textContent = translations[currentLang].error;
        };

    } else {
        console.error("Speech Recognition not supported.");
        chatStatus.textContent = translations[currentLang].noVoice;
        voiceBtn.style.display = "none";
    }

    // --- Sending Messages ---
    sendBtn.addEventListener('click', () => {
        const text = chatInput.value.trim();
        if (text) {
            addMessageToChat(text, 'user');
            sendTranscriptToModel(text, currentLang);
            chatInput.value = '';
        }
    });

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendBtn.click();
    });

    function addMessageToChat(message, sender) {
        const p = document.createElement('p');
        p.textContent = message;
        p.className = (sender === 'user') ? 'user-message' : 'bot-message';
        chatBody.appendChild(p);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // --- ML Model Connection Placeholder ---
    function sendTranscriptToModel(transcript, lang) {
        console.log(`Sending to Model [Lang: ${lang}]:`, transcript);

        // NOTE: When you connect your backend, pass the 'lang' variable too!
        // This helps your ML model know if it should process Hindi or English.
        
        setTimeout(() => {
            // Demo Logic for response
            let reply = "";
            const t = translations[lang];

            if (lang === 'hi-IN') {
                // Simple Hindi Keyword Demo
                if (transcript.includes("बैलेंस") || transcript.includes("खाता")) {
                    reply = "आपका वर्तमान बैलेंस ₹10,000 है।";
                } else {
                    reply = `आपने कहा: "${transcript}" (यह एक डेमो है)`;
                }
            } else {
                // Simple English Keyword Demo
                if (transcript.toLowerCase().includes("balance")) {
                    reply = "Your current balance is $10,000.";
                } else {
                    reply = `You said: "${transcript}" (This is a demo)`;
                }
            }
            
            addMessageToChat(reply, 'bot');
        }, 1000);
    }
});
document.addEventListener("DOMContentLoaded", function() {

    // --- CONFIGURATION ---
    // FIXED: Explicitly define the API URL.
    const API_URL = 'http://127.0.0.1:8000'; 
    // ---------------------

    // Get all necessary DOM elements
    const assistantIcon = document.getElementById('assistant-icon'); 
    const closeChatBtn = document.getElementById('close-chat'); 
    const chatBox = document.getElementById('chat-assistant-box');
    const chatInput = document.getElementById('chat-input');
    const chatBody = document.getElementById('chat-body');
    const sendBtn = document.getElementById('send-btn'); // FIXED: This element now exists in index.html
    const voiceBtn = document.getElementById('start-voice-btn');
    const languageSelector = document.getElementById('language-selector');
    
    // State variables for recording
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    
    // Helper function to get the current selected language
    function getCurrentLanguage() {
        return languageSelector.value;
    }

    // --- NEW CHATBOX TOGGLE LOGIC ---
    assistantIcon.addEventListener('click', () => {
        chatBox.classList.add('show');
        assistantIcon.style.display = 'none'; // Hide the floating icon
    });

    closeChatBtn.addEventListener('click', () => {
        chatBox.classList.remove('show');
        assistantIcon.style.display = 'flex'; // Show the floating icon
    });
    // ---------------------------------
    
    // --- Text Message ---
    // FIXED: Centralized function for text message sending
    function sendTextMessage(message) {
        if (message.trim() === '') return;

        addMessageToChat(message, 'user');
        chatInput.value = ''; // Clear input immediately
        
        // Disable input while waiting for response
        chatInput.disabled = true;
        
        fetch(`${API_URL}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                language: getCurrentLanguage(),
                user_id: "user" // Hardcoded for demo/user 1
            })
        })
        .then(response => response.json())
        .then(data => {
            addMessageToChat(data.response, 'bot');
            speakResponse(data.response);
        })
        .catch(error => {
            console.error("Text chat connection failed:", error);
            addMessageToChat("Connection failed. Is the FastAPI server running?", 'bot');
        })
        .finally(() => {
            chatInput.disabled = false;
            chatInput.focus();
        });
    }

    sendBtn.addEventListener('click', () => {
        sendTextMessage(chatInput.value);
    });

    // NEW: Add support for 'Enter' key press
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent default newline behavior
            sendTextMessage(chatInput.value);
        }
    });

    // --- Voice Message ---
    voiceBtn.addEventListener('click', () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    function startRecording() {
        audioChunks = [];
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                isRecording = true;
                
                voiceBtn.classList.add('recording');
                voiceBtn.innerHTML = '🔴 Stop'; // Simple text indicator for recording
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { 'type': 'audio/wav' });
                    sendAudioToServer(audioBlob);
                    stream.getTracks().forEach(track => track.stop()); // Stop the mic input stream
                };
            })
            .catch(error => {
                console.error("Microphone access failed:", error);
                alert("Microphone access denied or failed. Check browser permissions.");
            });
    }

    function stopRecording() {
        mediaRecorder.stop();
        isRecording = false;
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3.93-33-3-5.3 3c0 3.93-3.3 3-5.3 3S4 17 4 11H2c0 4.84 3.44 8.8 8 9.8V23h4v-2.2c4.56-1.01 8-4.97 8-9.8h-2z"/></svg>';
    }

    function sendAudioToServer(audioBlob) {
        addMessageToChat("Sending audio for transcription...", 'user');
        
        const formData = new FormData();
        formData.append("audio_file", audioBlob, "audio.wav");
        formData.append("language", getCurrentLanguage());
        formData.append("user_id", "user"); // Hardcoded for demo/user 1

        fetch(`${API_URL}/voice-chat/`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (!data.is_verified) {
                // Security Failure
                addMessageToChat("🚨 Voice Verification Failed: " + data.response, 'bot');
                speakResponse("Security check failed. " + data.response);
            } else {
                // Success
                addMessageToChat("✅ Verified. You said: " + data.transcription, 'user');
                addMessageToChat(data.response, 'bot');
                speakResponse(data.response);
            }
        })
        .catch(error => {
            console.error("Voice chat connection failed:", error);
            addMessageToChat("Connection failed. Is the FastAPI server running?", 'bot');
            speakResponse("I could not connect to the server.");
        })
    }

    // --- Utility Functions ---
    function addMessageToChat(message, sender) {
        const p = document.createElement('p');
        p.textContent = message;
        p.className = (sender === 'user') ? 'user-message' : 'bot-message';
        chatBody.appendChild(p);
        chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll
    }
    
    function speakResponse(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); 
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = getCurrentLanguage(); // Corrected: Use selected language for TTS
            window.speechSynthesis.speak(utterance);
        } else {
            console.warn("Browser does not support the Web Speech API for TTS.");
        }
    }
});
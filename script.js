document.addEventListener("DOMContentLoaded", function() {

    // Get all necessary DOM elements
    const assistantIcon = document.getElementById('assistant-icon'); // <-- NEW: Assistant icon to open chat
    const closeChatBtn = document.getElementById('close-chat'); // <-- NEW: Close button
    const chatBox = document.getElementById('chat-assistant-box');
    const chatInput = document.getElementById('chat-input');
    const chatBody = document.getElementById('chat-body');
    const sendBtn = document.getElementById('send-btn');
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
    sendBtn.addEventListener('click', () => {
        const text = chatInput.value.trim();
        if (text) {
            addMessageToChat(text, 'user');
            sendTextToModel(text);
            chatInput.value = '';
        }
    });

    // --- Voice Logic (Security Enabled) ---
    voiceBtn.addEventListener('click', async () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    // --- Voice Recording Functions ---
    async function startRecording() {
        if (isRecording) return; // Prevent double-click
        
        // **Critical: Request Microphone Access**
        try {
            // Check if MediaRecorder is available (modern browsers only)
            if (!window.MediaRecorder) {
                console.error("Browser does not support MediaRecorder.");
                addMessageToChat('Error: Your browser does not support voice input.', 'bot');
                return;
            }
            
            // This line triggers the browser's permission pop-up
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Successfully started stream, now start recording
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/wav' }); // Explicitly set mimeType
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                // Ensure all tracks are stopped to release the mic
                stream.getTracks().forEach(track => track.stop());

                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendAudioToModel(audioBlob);
            };

            mediaRecorder.start();
            isRecording = true;
            voiceBtn.innerHTML = '🛑'; // Change icon to stop (or text)
            addMessageToChat('🎙️ Recording... Click again when finished.', 'bot-status');
        
        } catch (error) {
            console.error('Microphone access denied or error:', error);
            // Display an informative error message to the user
            let errorMessage = 'Error: Could not access microphone.';
            if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
                errorMessage = '❌ Permission denied. Please enable microphone access for this site.';
            } else if (error.name === 'NotFoundError') {
                 errorMessage = '❌ No microphone found. Please connect one.';
            }
            addMessageToChat(errorMessage, 'bot');
            voiceBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1.2-9.1c0-.66.54-1.2 1.2-1.2s1.2.54 1.2 1.2l-.01 6.2c0 .66-.53 1.2-1.19 1.2s-1.2-.54-1.2-1.2V4.9zm6.5 6.1c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/></svg>'; // Reset button to SVG icon
            isRecording = false;
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            voiceBtn.innerHTML = '⚙️'; // Show processing icon/text
            addMessageToChat('Recording stopped. Processing...', 'bot-status');
        }
    }

    // --- API Interaction Functions ---
    async function sendTextToModel(text) {
        addMessageToChat("Processing text...", 'bot');
        
        const payload = {
            message: text,
            user_id: "user", // Hardcoded for demo
            language: getCurrentLanguage() // Corrected: Use selected language
        };
        
        try {
            const response = await fetch('http://127.0.0.1:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            addMessageToChat(data.response, 'bot');
            speakResponse(data.response);
        } catch (error) {
            console.error("Text chat connection failed:", error);
            addMessageToChat("Connection failed. Is the FastAPI server running?", 'bot');
            speakResponse("I could not connect to the server.");
        }
    }

    async function sendAudioToModel(audioBlob) {
        addMessageToChat("Processing voice security...", 'bot');
        voiceBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1.2-9.1c0-.66.54-1.2 1.2-1.2s1.2.54 1.2 1.2l-.01 6.2c0 .66-.53 1.2-1.19 1.2s-1.2-.54-1.2-1.2V4.9zm6.5 6.1c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/></svg>'; // Reset button icon here
        
        const formData = new FormData();
        formData.append("audio", audioBlob, "input.wav"); 
        formData.append("user_id", "user"); // Hardcoded user for demo
        formData.append("language", getCurrentLanguage()); // Corrected: Use selected language

        try {
            const response = await fetch('http://127.0.0.1:8000/voice-chat', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();

            if (data.verified === false) {
                // Security Failed
                addMessageToChat("❌ Voice Verification Failed: " + data.response, 'bot');
                speakResponse("Security check failed. " + data.response);
            } else {
                // Success
                addMessageToChat("✅ Verified. You said: " + data.transcription, 'user');
                addMessageToChat(data.response, 'bot');
                speakResponse(data.response);
            }
        } catch (error) {
            console.error("Voice chat connection failed:", error);
            addMessageToChat("Connection failed. Is the FastAPI server running?", 'bot');
            speakResponse("I could not connect to the server.");
        }
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
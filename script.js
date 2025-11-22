document.addEventListener("DOMContentLoaded", function() {

    const chatBox = document.getElementById('chat-assistant-box');
    const chatInput = document.getElementById('chat-input');
    const chatBody = document.getElementById('chat-body');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('start-voice-btn');
    
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // --- Text Message ---\r\n    sendBtn.addEventListener('click', () => {
        const text = chatInput.value.trim();
        if (text) {
            addMessageToChat(text, 'user');
            sendTextToModel(text);
            chatInput.value = '';
        }
    });

    // --- Voice Logic (Security Enabled) ---\r\n    voiceBtn.addEventListener('click', async () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendAudioToModel(audioBlob);
            };

            mediaRecorder.start();
            isRecording = true;
            voiceBtn.textContent = '🛑'; // Change icon to stop
            addMessageToChat('Recording...', 'bot-status');
        } catch (error) {
            console.error('Microphone access denied or error:', error);
            addMessageToChat('Error: Please allow microphone access.', 'bot');
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            voiceBtn.textContent = '🎤'; // Change icon back to mic
            addMessageToChat('Recording stopped. Processing...', 'bot-status');
        }
    }

    async function sendTextToModel(text) {
        addMessageToChat("Processing text...", 'bot');
        
        const payload = {
            message: text,
            user_id: "user",
            language: "en-US"
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
            speakResponse(data.response); // Speak the bot's text response
        } catch (error) {
            console.error(error);
            addMessageToChat("Connection failed.", 'bot');
            speakResponse("I could not connect to the server.");
        }
    }

    async function sendAudioToModel(audioBlob) {
        addMessageToChat("Processing voice security...", 'bot'); // Feedback
        
        const formData = new FormData();
        // File name must end in .wav or .webm depending on browser
        formData.append("audio", audioBlob, "input.wav"); 
        formData.append("user_id", "user"); // Hardcoded user for now
        formData.append("language", "en-US");

        try {
            const response = await fetch('http://127.0.0.1:8000/voice-chat', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();

            if (data.verified === false) {
                // Security Failed
                addMessageToChat("❌ " + data.response, 'bot');
                speakResponse("Security check failed. " + data.response); // Speak failure message
            } else {
                // Success
                addMessageToChat("✅ Verified. You said: " + data.transcription, 'user');
                addMessageToChat(data.response, 'bot');
                speakResponse(data.response); // <--- ADDED: Speak the bot's final response
            }
        } catch (error) {
            console.error(error);
            addMessageToChat("Connection failed.", 'bot');
            speakResponse("I could not connect to the server.");
        }
    }

    function addMessageToChat(message, sender) {
        const p = document.createElement('p');
        p.textContent = message;
        p.className = (sender === 'user') ? 'user-message' : 'bot-message';
        chatBody.appendChild(p);
        chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll to latest message
    }
    
    // --- NEW TEXT-TO-SPEECH FUNCTION ---
    function speakResponse(text) {
        if ('speechSynthesis' in window) {
            // Stop any currently speaking audio before starting a new one
            window.speechSynthesis.cancel(); 
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US'; 
            window.speechSynthesis.speak(utterance);
        } else {
            console.warn("Browser does not support the Web Speech API for TTS.");
        }
    }

});
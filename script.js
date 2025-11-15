document.addEventListener("DOMContentLoaded", function() {

    // --- Chatbox Toggle Logic ---
    const assistantIcon = document.getElementById('assistant-icon');
    const chatBox = document.getElementById('chat-assistant-box');
    const closeChatButton = document.getElementById('close-chat');

    function toggleChatbox() {
        chatBox.classList.toggle('show');
    }

    assistantIcon.addEventListener('click', toggleChatbox);
    closeChatButton.addEventListener('click', toggleChatbox);


    

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    

    const voiceBtn = document.getElementById('start-voice-btn');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBody = document.getElementById('chat-body');
    const chatStatus = document.getElementById('chat-status');

    if (SpeechRecognition) {
        console.log("Speech Recognition is supported.");
        const recognition = new SpeechRecognition();
        
        
        recognition.interimResults = false; // We only want final results
        recognition.lang = 'en-US';

        
        voiceBtn.addEventListener('click', () => {
            try {
                recognition.start();
            } catch (error) {
                console.error("Recognition already started.", error);
            }
        });

        
        recognition.onstart = () => {
            chatStatus.textContent = "Listening...";
            voiceBtn.classList.add('listening');
        };

        
        recognition.onend = () => {
            chatStatus.textContent = ""; 
            voiceBtn.classList.remove('listening');
        };

        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            
            
            addMessageToChat(transcript, 'user');
            
            
            sendTranscriptToModel(transcript);
        };

        
        recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            if (event.error === 'no-speech' || event.error === 'audio-capture') {
                chatStatus.textContent = "No speech detected. Please try again.";
            } else {
                chatStatus.textContent = "Error: " + event.error;
            }
        };

    } else {
        
        console.error("Speech Recognition is not supported in this browser.");
        chatStatus.textContent = "Voice input not supported.";
        voiceBtn.disabled = true;
        voiceBtn.style.display = "none";
    }
    
    
    
    
    sendBtn.addEventListener('click', () => {
        const text = chatInput.value.trim();
        if (text) {
            addMessageToChat(text, 'user');
            sendTranscriptToModel(text); // Use the same function as voice
            chatInput.value = '';
        }
     });


    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendBtn.click(); 
        }
    });


    /**
     * 
     * @param {string} message
     * @param {string} sender 
     */
    function addMessageToChat(message, sender) {
        const p = document.createElement('p');
        p.textContent = message;
        p.className = (sender === 'user') ? 'user-message' : 'bot-message';
        chatBody.appendChild(p);
        
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    /**
     * ! Placeholder function for your ML model !
     * This is where you would send the text (from voice or typing) to your backend.
     */
    function sendTranscriptToModel(transcript) {
        console.log("Sending to ML model:", transcript);
        
        // --- TODO: ---
        // This is where you would use `fetch` to call your ML model's API:
        //
        // fetch('/api/your-ml-model', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ text: transcript })
        // })
        // .then(response => response.json())
        // .then(data => {
        //     addMessageToChat(data.reply, 'bot');
        // })
        // .catch(error => console.error('Error with ML model:', error));


        // --- DEMO BOT RESPONSE ---
        // We'll simulate a bot response after 1 second.
        setTimeout(() => {
            let botReply = `You said: "${transcript}" (This is a demo response.)`;
            
            // Add some simple demo logic
            if (transcript.toLowerCase().includes('balance')) {
                botReply = "Your current demo balance is $10,450.50.";
            } else if (transcript.toLowerCase().includes('hello')) {
                botReply = "Hi there! How can I assist you today?";
            }

            addMessageToChat(botReply, 'bot');
        }, 1000);
    }

});
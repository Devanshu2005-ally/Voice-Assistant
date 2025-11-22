def dialog_manager(intent, slots):
    """
    Dialog Manager:
    - Checks for required slots
    - If missing, asks user via speech
    - If complete, calls the API and returns response
    """
    # Define required slots for each intent
    REQUIRED_SLOTS = {
        "transfer": ["amount", "recipient", "account_number"],
        "check_balance": [],
        "check_transactions": ["start_date", "end_date"],

        #for loan inquiry intent
        "loan types": [],
        "loan_interest_rate": ["loan_type"],
        "loan_eligibility": ["loan_type", "income", "credit_score"],
        "loan_status": ["user_id"],
        "loan_required_documents": ["loan_type"],
        "loan_processing_time": ["loan_type"],


        #for credit card intent
        "credit_check": ["card_type", "card_name"],
        "credit_limit_available": ["card_type", "card_name"],
        "credit_limit_used": ["card_type", "card_name"],
        "credit_limit_increase": ["card_type", "card_name", "requested_increase_amount"],
        "credit_eligibility": ["card_type", "income", "credit_score"]
        
        #for payment alerts
    }






def speak(text):
    # Generate speech in memory
    mp3_fp = BytesIO()
    tts = gTTS(text=sent, lang='en')
    tts.write_to_fp(mp3_fp)

    # Load into pydub without saving
    mp3_fp.seek(0)
    audio = AudioSegment.from_file(mp3_fp, format="mp3")

    # Play audio
    play_obj = sa.play_buffer(
        audio.raw_data,
        num_channels=audio.channels,
        bytes_per_sample=audio.sample_width,
        sample_rate=audio.frame_rate
    )
    play_obj.wait_done()



def transcribe_and_translate():
    model = whisper.load_model("base")
    result = model.transcribe("new_cleaned.wav", task = 'translate')
    text = result["text"]
    detected_lang = result["language"]
    print(f"Detected language: {detected_lang}")
    print(f"Original text: {text}")
    intent = predict_intent(text)
    slot_pairs = predict_slots(text)
    slots = extract_slot_dict(slot_pairs)
    print(f"Predicted Intent: {intent}")
    print(f"Extracted Slots: {slots}")
    return intent, slots, text

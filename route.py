import requests


USER_ID = 1

def route_to_api(intent, slots):
    """
    Routes the intent and slots to the appropriate API endpoint.
    """
    if intent == "transfer":
        url = "http://localhost:8000/transfer"

    elif intent == "check_balance":
        url = "http://localhost:8000/balance"
    elif intent == "check_transactions":
        url = "http://localhost:8000/transactions"
    else:
        return "Unknown intent"

    payload = {
        "user_id": USER_ID,
        **slots
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result =  response.json()
        return result
    except requests.RequestException as e:
        return f"API request failed: {e}"
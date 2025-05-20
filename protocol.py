import json
import time

def current_timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def create_message(msg_type, sender='', content='', timestamp=None):
    if timestamp is None:
        timestamp = current_timestamp()
    return json.dumps({
        'type': msg_type,    # "register", "login", "message", "history", "system", "error"
        'sender': sender,
        'content': content,
        'timestamp': timestamp
    })

def parse_message(msg_json):
    try:
        return json.loads(msg_json)
    except json.JSONDecodeError:
        return None
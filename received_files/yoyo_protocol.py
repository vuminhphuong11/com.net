import json
import time
import base64

def current_timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def create_message(msg_type, sender='', content='', timestamp=None):
    if timestamp is None:
        timestamp = current_timestamp()
    return json.dumps({
        'type': msg_type,    
        'sender': sender,
        'content': content,
        'timestamp': timestamp
    })

def create_file_message (sender, filename, filetype, file_bytes, timestamp=None):
    if timestamp is None:
        timestamp = current_timestamp()
    content = base64.b64encode(file_bytes).decode('utf-8')
    return json.dumps({
        'type':'file',
        'sender': sender,
        'filename': filename,
        'filetype': filetype,
        'content': content,
        'timestamp': timestamp,
        'filesize': len(file_bytes)
    })

def parse_message(msg_json):
    try:
        msg = json.loads(msg_json)
        return msg
    except json.JSONDecodeError:
        return None

def parse_file_message(msg_json):
    try:
        if msg_json is None:
            return None
        msg = json.loads(msg_json)
        if msg.get('type') == 'file' and 'content' in msg:
            try:
                msg['file_bytes'] = base64.b64decode(msg['content'])
            except Exception as e:
                print(f"Error decoding file content: {e}")
                return None
        return msg
    except (json.JSONDecodeError, Exception):
        return None
    
def validate_message(msg):
    if not isinstance(msg, dict):
        return False
        
    required_fields = ['type']
    for field in required_fields:
        if field not in msg:
            return False
   
    if msg['type'] == 'file':
        file_required = ['sender', 'filename', 'content']
        for field in file_required:
            if field not in msg:
                return False
    elif msg['type'] in ['message', 'register', 'login']:
        if 'sender' not in msg:
            return False
            
    return True
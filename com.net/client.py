import socket
import threading
import protocol
import os
import mimetypes
from security import encrypt_message, decrypt_message
import base64

EMOJI_LIST = [
    "😄",  
    "😢",  
    "❤️",  
    "👍",  
    "😆",  
    "😉",  
    "😭",  
    "😠",  
    "😂",  
    "😍",  
    "😊",  
    "😎",  
    "😞",  
    "😜",  
    "😇",  
    "😏",  
    "😮", 
    "😴", 
    "🤔", 
    "🤗",  
]

MAX_FILE_SIZE = 10*1024*1024#bit
ALLOWED_MIME_PREFIXES = ['image/', 'audio/', 'video/', 'text/', 'application/pdf']

def send_message_with_length(sock, message):
    try:
        encrypted = encrypt_message(message)
        msg_bytes = encrypted.encode('utf-8')
        length = len(msg_bytes)
        sock.sendall(length.to_bytes(4, 'big') + msg_bytes)
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def recv_message_with_length(sock):
    try:
        length_bytes = b''
        while len(length_bytes) < 4:
            chunk = sock.recv(4 - len(length_bytes))
            if not chunk:
                return None
            length_bytes += chunk

        length = int.from_bytes(length_bytes, 'big')
        if length > 10 * 1024 * 1024:
            print(f"Message too large: {length} bytes")
            return None

        message_bytes = b''
        while len(message_bytes) < length:
            chunk = sock.recv(min(4096, length - len(message_bytes)))
            if not chunk:
                return None
            message_bytes += chunk

        encrypted_message = message_bytes.decode('utf-8')
        decrypted = decrypt_message(encrypted_message)
        return decrypted
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

def send_protocol_message(sock, msg_type, sender='', content=''):
    msg = protocol.create_message(msg_type, sender, content)
    return send_message_with_length(sock, msg)

def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"
    
def receive_messages(sock, username):
    while True:
        try:
            msg_json = recv_message_with_length(sock)
            if msg_json is None:
                print("\nDisconnected from server (socket closed).")
                break
            
            msg = protocol.parse_message(msg_json)
            if msg is None:
                print("\nReceived invalid message format")
                continue
                
            if msg['type'] == 'file':
                filename = msg.get('filename', 'received_file')
                sender = msg.get('sender', 'Unknown')
                file_content_base64 = msg.get('content', '')
                filetype = msg.get('filetype', 'unknown')
                timestamp = msg.get('timestamp', '')
                
                try: 
                    file_bytes = base64.b64decode(file_content_base64)
                    file_size = len(file_bytes)
                    
                    os.makedirs('received_files', exist_ok=True)
                    
                    safe_filename = f"{sender}_{filename}"
                    save_path = os.path.join('received_files', safe_filename)
                    
                    with open(save_path, 'wb') as f:
                        f.write(file_bytes)
                    
                    print(f"\n[{timestamp}] {sender} shared a file:")
                    print(f"File: {filename}")
                    print(f"Size: {format_file_size(file_size)}")
                    print(f"Type: {filetype}")
                    print(f"Saved as: {save_path}")
                    
                except Exception as e:
                    print(f"\n[Failed to save file from {sender}: {e}]")
                    
            elif msg['type'] in ('message', 'history'):
                print(f"\n[{msg['timestamp']}] [{msg['sender']}]: {msg['content']}")
            else:
                print(f"\n[System]: {msg['content']}")
            print(f"{username}: ", end="", flush=True)
        except Exception as e:
            print(f"\nException in receive_messages: {e}")
            import traceback
            traceback.print_exc()
            break
               
def emoji_picker():
    print("\nEmoji Picker:")
    for i, emoji_char in enumerate(EMOJI_LIST, start=1):
        print(f"{i}. {emoji_char}")
    choice = input("Select emoji number (from 1 to 20) or Press any other keys to cancel: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(EMOJI_LIST):
            return EMOJI_LIST[idx]
    print("Invalid choice. No emoji selected.")
    return ""

def process_message_with_emojis(message):
    current_message = message
    has_emoji = "/emoji" in current_message

    while "/emoji" in current_message:
        emoji_char = emoji_picker()
        if emoji_char == "":
            current_message = current_message.replace("/emoji", "", 1)
        else:
            current_message = current_message.replace("/emoji", emoji_char, 1)
    
    if has_emoji:
        while True:
            print(f"\nYour message: {current_message}")
            edit_input = input("Press Enter to send, or edit your message: ").strip()
            
            if edit_input == "":
                return current_message
            else:
                current_message = edit_input
                while "/emoji" in current_message:
                    emoji_char = emoji_picker()
                    if emoji_char == "":
                        current_message = current_message.replace("/emoji", "", 1)
                    else:
                        current_message = current_message.replace("/emoji", emoji_char, 1)
    
    return current_message

def send_file(sock, sender, filepath):
    if not os.path.isfile(filepath):
        print("File not found")
        return
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    if filesize > MAX_FILE_SIZE:#10mb
        print(f"File too large ({filesize} bytes). Max allowed is {MAX_FILE_SIZE} bytes")
        return
    if not is_allowed_filetype(filepath):
        print("File type not allowed")
        return
    print(f"Uploading {filename} ({format_file_size(filesize)})...")
    try:
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
        
        filetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
        msg = protocol.create_file_message(sender, filename, filetype, file_bytes)
        
        if send_message_with_length(sock, msg):
            print(f"File sent successfully: {filename}")
            return True
        else:
            print(f"Failed to send file: {filename}")
            return False
    except Exception as e:
        print(f"Error sending file: {e}")
        return False

def is_allowed_filetype(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
        return False
    return any(mime_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES)

def list_received_files():
    files_dir = 'received_files'
    if not os.path.exists(files_dir):
        print("No received files directory found.")
        return
    
    files = os.listdir(files_dir)
    if not files:
        print("No received files found.")
        return
    
    print("\nReceived Files:")
    print("-" * 50)
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(files_dir, filename)
        filesize = os.path.getsize(filepath)
        print(f"{i:2}. {filename} ({format_file_size(filesize)})")
    print("-" * 50)

def show_help():
    print("\nAvailable Commands:")
    print("Regular message - just type and press Enter")
    print("/emoji - insert emoji in your message")  
    print("/sendfile <path> - send a file to all users")
    print("/files - list all received files")
    print("/members - show online members")
    print("/help - show this help message")
    print("/quit or /exit - leave the chat")

def main():
    host = 'localhost'
    port = 12345
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((host, port))
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return

    while True:
        print("1. Register")
        print("2. Login")
        choice = input("Choose 1 or 2: ").strip()
        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            send_protocol_message(client_socket, 'register', username, password)
            response_json = recv_message_with_length(client_socket)
            if response_json is None:
                print("No response from server.")
                client_socket.close()
                return
            response = protocol.parse_message(response_json)
            if response is None:
                print("Invalid response from server.")
                client_socket.close()
                return
            print(f"[Server]: {response['content']}")
            client_socket.close()
            return
        elif choice == '2':
            username = input("Username: ")
            password = input("Password: ")
            send_protocol_message(client_socket, 'login', username, password)
            response_json = recv_message_with_length(client_socket)
            if response_json is None:
                print("No response from server.")
                client_socket.close()
                return
            response = protocol.parse_message(response_json)
            if response is None:
                print("Invalid response from server.")
                client_socket.close()
                return
            if response['content'] == 'Login successful!':
                print("[Server]: Login successful! Starting chat...")
                break
            else:
                print(f"[Server]: {response['content']}")
                client_socket.close()
                return
        else:
            print("Invalid choice, please select 1 or 2.")

    recv_thread = threading.Thread(target=receive_messages, args=(client_socket, username))
    recv_thread.daemon = True
    recv_thread.start()

    try:
        while True:
            message = input(f"{username}: ").strip()

            if message.startswith('/sendfile '):
                filepath = message[len('/sendfile '):].strip()
                send_file(client_socket, username, filepath)
                continue

            if message == '/help':
                show_help()
                continue

            if message == '/members':
                send_protocol_message(client_socket, 'message', username, '/members')
                continue
            
            if message.lower() in ('/quit', '/exit'):
                print("Exiting chat...")
                break

            if message:
                final_message = process_message_with_emojis(message)
                if not send_protocol_message(client_socket, 'message', username, final_message):
                    print("Failed to send message. Connection lost.")
                    break
    except KeyboardInterrupt:
        print("\nExiting chat...")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    main()
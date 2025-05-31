import socket
import json
from security import encrypt_message, decrypt_message

HOST = 'localhost'
PORT = 12345
client_socket = None

def create_socket_if_needed():
    global client_socket
    if client_socket is None or getattr(client_socket, '_closed', True): 
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((HOST, PORT))
        except ConnectionRefusedError:
            print(f"Connection refused from {HOST}:{PORT}. Is server running?")
            client_socket = None 
            raise 
    return client_socket

def close_socket():
    global client_socket
    if client_socket:
        try:
            client_socket.close()
        except OSError:
            pass 
        client_socket = None

def reconnect_socket():
    close_socket()
    create_socket_if_needed()

def send_msg_framed(sock, message_str):
    if sock is None: return False
    try:
        encrypted = encrypt_message(message_str)
        msg_bytes = encrypted.encode('utf-8')
        length = len(msg_bytes)
        sock.sendall(length.to_bytes(4, 'big') + msg_bytes)
        return True
    except Exception as e:
        print(f"Error sending framed message: {e}")
        close_socket() 
        return False


def recv_msg_framed(sock):
    if sock is None: return None
    try:
        length_bytes = b''
        while len(length_bytes) < 4:
            chunk = sock.recv(4 - len(length_bytes))
            if not chunk: return None
            length_bytes += chunk
        length = int.from_bytes(length_bytes, 'big')

        if length > 20 * 1024 * 1024: 
            print(f"Message too large: {length} bytes. Closing socket.")
            close_socket()
            return None

        message_bytes = b''
        while len(message_bytes) < length:
            chunk = sock.recv(min(4096, length - len(message_bytes)))
            if not chunk: return None 
            message_bytes += chunk

        encrypted_data = message_bytes.decode('utf-8')
        return decrypt_message(encrypted_data)
    except ConnectionResetError:
        print("Connection reset by peer.")
        close_socket()
        return None
    except Exception as e:
        print(f"Error receiving framed message: {e}")
        close_socket()
        return None

def send_auth_request(request_dict):
    global client_socket
    try:
        if client_socket is None:
             create_socket_if_needed()

        if not client_socket: 
            return '{"type": "error", "content": "Failed to connect to server."}'

        message_str = json.dumps(request_dict)
        if not send_msg_framed(client_socket, message_str):
            return '{"type": "error", "content": "Failed to send request."}'

        response_str = recv_msg_framed(client_socket)
        if response_str is None:
            return '{"type": "error", "content": "No response or connection closed."}'
        return response_str
    except ConnectionRefusedError:
        return '{"type": "error", "content": "Connection refused. Server may be down."}'
    except Exception as e:
        print(f"Unhandled error in send_auth_request: {e}")
        return f'{{"type": "error", "content": "Client-side auth error: {e}"}}'

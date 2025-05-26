import socket
import threading
import protocol
import database
import traceback
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
import base64

host = '0.0.0.0'
port = 12345
# khóa
DES_KEY = b'8bytekey'
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(5)
clients = []
usernames = {}
def des_encrypt(data):
    cipher = DES.new(DES_KEY, DES.MODE_ECB)
    padded_data = pad(data.encode('utf-8'), DES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return base64.b64encode(encrypted)  # encode thành chuỗi base64
def des_decrypt(data):
    cipher = DES.new(DES_KEY, DES.MODE_ECB)
    decoded = base64.b64decode(data)  # decode từ base64 về bytes
    decrypted_padded = cipher.decrypt(decoded)
    decrypted = unpad(decrypted_padded, DES.block_size)
    return decrypted.decode('utf-8')

def broadcast(message_dict, sender_socket=None):
    if isinstance(message_dict, dict):
        msg_str = protocol.create_message(**message_dict)
    else:
        msg_str = message_dict
    for client in clients[:]:
        if client != sender_socket:
            try:
                client.send(des_encrypt(msg_str))
            except:
                try:
                    client.close()
                except:
                    pass
                if client in clients:
                    clients.remove(client)

def list_online_members():
    return ', '.join(usernames.values())

def handle_client(client_socket):
    try:
        data = client_socket.recv(1024)
        data = des_decrypt(data)  
        command = protocol.parse_message(data)
        if command is None or 'type' not in command:
            client_socket.send(des_encrypt(protocol.create_message('error', content='Invalid command format')))
            client_socket.close()
            return
        if command['type'] == 'register':
            username = command['sender']
            password = command['content']
            if database.add_user(username, password):
                resp = protocol.create_message('system', content='Register successful!')
            else:
                resp = protocol.create_message('error', content='Username already exists.')
            client_socket.send(des_encrypt(resp))
            client_socket.close()
            return
        elif command['type'] == 'login':
            username = command['sender']
            password = command['content']
            if database.check_user(username, password):
                resp = protocol.create_message('system', content='Login successful!')
                client_socket.send(des_encrypt(resp))
                usernames[client_socket] = username
                clients.append(client_socket)
                broadcast(protocol.create_message('system', content=f'{username} joined the chat.'), client_socket)
                history = database.get_recent_messages()
                for sender, content, timestamp in history:
                    msg = protocol.create_message('history', sender=sender, content=content, timestamp=timestamp)
                    client_socket.send(des_encrypt(msg))
            else:
                resp = protocol.create_message('error', content='Invalid username or password.')
                client_socket.send(des_encrypt(resp))
                client_socket.close()
                return
        else:
            client_socket.send(des_encrypt(protocol.create_message('error', content='Unknown command')))
            client_socket.close()
            return
        while True:
            msg_data = client_socket.recv(1024)
            if not msg_data:
                break
            msg_data = des_decrypt(msg_data)
            msg = protocol.parse_message(msg_data)
            if msg is None:
                client_socket.send(des_encrypt(protocol.create_message('error', content='Invalid message format')))
                continue
            if msg['content'].lower() in ('/quit', '/exit'):
                break
            if msg['content'] == '/members':
                online = list_online_members()
                client_socket.send(des_encrypt(protocol.create_message('system', content=f'Online: {online}')))
            else:
                database.save_message(usernames[client_socket], msg['content'], msg['timestamp'])
                broadcast({'msg_type': 'message', 'sender': usernames[client_socket], 'content': msg['content'], 'timestamp': msg['timestamp']}, client_socket)
    except Exception as e:
        print(f"Error in client handler: {e}")
        traceback.print_exc()
    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        left_user = usernames.pop(client_socket, 'Unknown')
        broadcast(protocol.create_message('system', content=f'{left_user} left the chat.'))
        client_socket.close()

def receive_connections():
    print(f'Server listening on {host}:{port}...')
    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == '__main__':
    receive_connections()

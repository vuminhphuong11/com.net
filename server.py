import socket
import threading
import protocol
import database
import traceback

host = '0.0.0.0'
port = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((host, port))
server_socket.listen(5)

clients = []
usernames = {}
clients_lock = threading.Lock()

def send_message_with_length(sock, message):
    try:
        msg_bytes = message.encode('utf-8')
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

        return message_bytes.decode('utf-8')
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

def broadcast(message_dict, sender_socket=None):
    with clients_lock:
        if isinstance(message_dict, dict):
            if message_dict.get('type') == 'file':
                msg_str = protocol.create_file_message(
                    message_dict['sender'],
                    message_dict['filename'],
                    message_dict['filetype'],
                    message_dict['file_bytes'],
                    message_dict['timestamp']
                )
            else:
                msg_str = protocol.create_message(
                    message_dict['type'],
                    message_dict.get('sender', ''),
                    message_dict.get('content', ''),
                    message_dict.get('timestamp')
                )
        else:
            msg_str = message_dict

        failed_clients = []
        for client in clients[:]:
            if not send_message_with_length(client, msg_str):
                failed_clients.append(client)

        for client in failed_clients:
            remove_client(client)

def remove_client(client_socket):
    try:
        with clients_lock:
            if client_socket in clients:
                clients.remove(client_socket)
            username = usernames.pop(client_socket, 'Unknown')
        client_socket.close()
        return username
    except Exception as e:
        print(f"Error removing client: {e}")
        return 'Unknown'

def list_online_members():
    with clients_lock:
        return ', '.join(usernames.values())

def handle_client(client_socket):
    try:
        data = recv_message_with_length(client_socket)
        print(f"[SERVER DEBUG] Received initial data: {data}")
        if data is None:
            client_socket.close()
            return

        command = protocol.parse_message(data)
        print(f"[SERVER DEBUG] Parsed initial command: {command}")
        if command is None or 'type' not in command:
            send_message_with_length(
                client_socket,
                protocol.create_message('error', content='Invalid command format'))
            client_socket.close()
            return

        if command['type'] == 'register':
            username = command['sender']
            password = command['content']
            if database.add_user(username, password):
                resp = protocol.create_message('system', content='Register successful!')
            else:
                resp = protocol.create_message('error', content='Username already exists.')
            send_message_with_length(client_socket, resp)
            client_socket.close()
            return

        elif command['type'] == 'login':
            username = command['sender']
            password = command['content']
            if database.check_user(username, password):
                resp = protocol.create_message('system', content='Login successful!')
                send_message_with_length(client_socket, resp)

                with clients_lock:
                    usernames[client_socket] = username
                    clients.append(client_socket)

                broadcast({
                    'type': 'system',
                    'content': f'{username} joined the chat.',
                    'sender': 'System',
                    'timestamp': protocol.current_timestamp()
                }, client_socket)

                history = database.get_recent_messages()
                for sender, content, timestamp in history:
                    msg = protocol.create_message('history', sender=sender, content=content, timestamp=timestamp)
                    send_message_with_length(client_socket, msg)

                print(f"[DEBUG] {username} has logged in. Waiting for messages...")
                while True:
                    msg_data = recv_message_with_length(client_socket)
                    print(f"[SERVER DEBUG] Raw received from {username}: {msg_data}")
                    if msg_data is None:
                        break

                    msg = protocol.parse_message(msg_data)
                    print(f"[SERVER DEBUG] Parsed message: {msg}")
                    if msg is None:
                        send_message_with_length(
                            client_socket,
                            protocol.create_message('error', content='Invalid message format'))
                        continue

                    if msg.get('type') == 'file':
                        try:
                            file_msg = protocol.parse_file_message(msg_data)
                            if file_msg is None:
                                send_message_with_length(
                                    client_socket,
                                    protocol.create_message('error', content="Invalid file message"))
                                continue

                            file_bytes = file_msg.get('file_bytes', b'')
                            filesize = len(file_bytes)

                            with clients_lock:
                                current_username = usernames.get(client_socket, 'Unknown')

                            database.save_file_metadata(
                                current_username,
                                file_msg['filename'],
                                file_msg['filetype'],
                                filesize,
                                file_msg['timestamp']
                            )

                            broadcast({
                                'type': 'file',
                                'sender': current_username,
                                'filename': file_msg['filename'],
                                'filetype': file_msg['filetype'],
                                'file_bytes': file_bytes,
                                'timestamp': file_msg['timestamp']
                            }, client_socket)

                            send_message_with_length(
                                client_socket,
                                protocol.create_message('system', content=f"File '{file_msg['filename']}' shared successfully!")
                            )

                            print(f"File {file_msg['filename']} ({filesize} bytes) shared by {current_username}")
                        except Exception as e:
                            print(f"Error handling file message: {e}")
                            send_message_with_length(client_socket,
                                protocol.create_message('error', content="Error processing file"))
                        continue

                    if msg['content'].lower() in ('/quit', '/exit'):
                        break

                    if msg['content'] == '/members':
                        online = list_online_members()
                        send_message_with_length(
                            client_socket,
                            protocol.create_message('system', content=f'Online: {online}'))
                        continue

                    with clients_lock:
                        current_username = usernames.get(client_socket, 'Unknown')

                    database.save_message(current_username, msg['content'], msg['timestamp'])
                    broadcast({
                        'type': 'message',
                        'sender': current_username,
                        'content': msg['content'],
                        'timestamp': msg['timestamp']
                    }, client_socket)
            else:
                resp = protocol.create_message('error', content='Invalid username or password.')
                send_message_with_length(client_socket, resp)
                client_socket.close()
                return
        else:
            send_message_with_length(
                client_socket,
                protocol.create_message('error', content='Unknown command'))
            client_socket.close()
            return

    except Exception as e:
        print(f"Error in client handler: {e}")
        traceback.print_exc()
    finally:
        left_user = remove_client(client_socket)
        if left_user != 'Unknown':
            broadcast({
                'type': 'system',
                'content': f'{left_user} left the chat.',
                'sender': 'System',
                'timestamp': protocol.current_timestamp()
            })

def receive_connections():
    print(f'Server listening on {host}:{port}...')
    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"New connection from {addr}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()

if __name__ == '__main__':
    receive_connections()

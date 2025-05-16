import socket
import threading
import json

#dữ liệu người dùng
def load_users():
    try:
        with open('user.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open('user.json', 'w') as f:
        json.dump(users, f)

def check_login(username, password):
    users = load_users()
    return users.get(username) == password

def register_user(username, password):
    users = load_users()
    if username in users:
        return False  
    users[username] = password
    save_users(users)
    return True

#socket server
host = '0.0.0.0'
port = 12345
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(5)

print(f"[STARTED] Server is listening on {host}:{port}")

#quản lý client
clients = []
usernames = {}

def broadcast(message, sender_socket=None):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except:
                client.close()
                clients.remove(client)

def list_online_members():
    return ', '.join(usernames.values())

def handle_client(client_socket):
    try:
        #nhận yêu cầu: REGISTER hoặc LOGIN
        command = client_socket.recv(1024).decode('utf-8')

        if command == "REGISTER":
            username = client_socket.recv(1024).decode('utf-8')
            password = client_socket.recv(1024).decode('utf-8')
            if not username or not password:
                client_socket.send("Invalid input. Try again.".encode('utf-8'))
            else:
                if register_user(username, password):
                    client_socket.send("Register successful!".encode('utf-8'))
                else:
                    client_socket.send("Username already exists.".encode('utf-8'))
            client_socket.close()
            return

        elif command == "LOGIN":
            username = client_socket.recv(1024).decode('utf-8')
            password = client_socket.recv(1024).decode('utf-8')
            if check_login(username, password):
                client_socket.send("Login successful!".encode('utf-8'))
                usernames[client_socket] = username
                clients.append(client_socket)
                print(f"[LOGIN] {username} has connected.")
                broadcast(f"[SYSTEM] {username} has joined the chat.")
                client_socket.send(f"Currently online: {list_online_members()}".encode('utf-8'))
            else:
                client_socket.send("Invalid username or password.".encode('utf-8'))
                client_socket.close()
                return
        else:
            client_socket.send("Unknown command.".encode('utf-8'))
            client_socket.close()
            return

        #chat loop
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"[{usernames[client_socket]}] {message}")
                if message == "/members":
                    member_list = list_online_members()
                    client_socket.send(f"[SYSTEM] Online: {member_list}".encode('utf-8'))
                else:
                    broadcast(f"[{usernames[client_socket]}] {message}", client_socket)
            else:
                break

    except:
        pass
    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        left_user = usernames.pop(client_socket, "Unknown")
        broadcast(f"[SYSTEM] {left_user} has left the chat.")
        client_socket.close()
        print(f"[DISCONNECT] {left_user} disconnected.")

def receive_connections():
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"[NEW CONNECTION] {client_address} connected.")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

receive_connections()
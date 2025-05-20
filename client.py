import socket
import threading
import protocol

def send_protocol_message(sock, msg_type, sender='', content=''):
    msg = protocol.create_message(msg_type, sender, content)
    sock.send(msg.encode('utf-8'))

def receive_messages(sock, username):
    while True:
        try:
            msg_json = sock.recv(1024).decode('utf-8')
            msg = protocol.parse_message(msg_json)
            if msg:
                if msg['type'] in ('message', 'history'):
                    print(f"\n[{msg['timestamp']}] [{msg['sender']}]: {msg['content']}")
                else:
                    print(f"\n[System]: {msg['content']}")
                print(f"{username}: ", end="", flush=True)
        except:
            print("\nDisconnected from server.")
            sock.close()
            break

def main():
    host = 'localhost'
    port = 12345
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    while True:
        print("1. Register")
        print("2. Login")
        choice = input("Choose 1 or 2: ").strip()
        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            send_protocol_message(client_socket, 'register', username, password)
            response_json = client_socket.recv(1024).decode('utf-8')
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
            response_json = client_socket.recv(1024).decode('utf-8')
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
            if message.lower() in ('/quit', '/exit'):
                print("Exiting chat...")
                client_socket.close()
                break
            if message:
                send_protocol_message(client_socket, 'message', username, message)
    except KeyboardInterrupt:
        print("\nExiting chat...")
        client_socket.close()

if __name__ == '__main__':
    main()
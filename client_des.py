import socket
import threading
import protocol
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
import base64
# chìa khóa phải gồm 64 bit tức là 8 ký tự nhé với lại khóa ở đây phải giống với file server
DES_KEY = b'8bytekey'
# mã hóa và giải mã
def des_encrypt(data):
    cipher = DES.new(DES_KEY, DES.MODE_ECB)
    padded_data = pad(data.encode('utf-8'), DES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return base64.b64encode(encrypted)  # mã hóa Base64 sau khi DES
def des_decrypt(data):
    cipher = DES.new(DES_KEY, DES.MODE_ECB)
    decoded = base64.b64decode(data)  # giải mã Base64 trước
    decrypted_padded = cipher.decrypt(decoded)
    decrypted = unpad(decrypted_padded, DES.block_size)
    return decrypted.decode('utf-8')

def send_protocol_message(sock, msg_type, sender='', content=''):
    msg = protocol.create_message(msg_type, sender, content)
    sock.send(des_encrypt(msg))

def receive_messages(sock, username):
    while True:
        try:
            msg_data = sock.recv(1024)
            if not msg_data:
                print("\nDisconnected from server.")
                break
            msg_json = des_decrypt(msg_data)  # giả sử des_decrypt nhận bytes và trả về string JSON
            msg = protocol.parse_message(msg_json)
            if msg:
                if msg['type'] in ('message', 'history'):
                    print(f"\n[{msg['timestamp']}] [{msg['sender']}]: {msg['content']}")
                else:
                    print(f"\n[System]: {msg['content']}")
                print(f"{username}: ", end="", flush=True)
        except Exception as e:
            print("\nDisconnected from server or error:", e)
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
            response_data = client_socket.recv(1024)
            response_json = des_decrypt(response_data)
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
            response_data = client_socket.recv(1024)
            response_json = des_decrypt(response_data)
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

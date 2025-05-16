import socket
import time
import threading

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))

while True:
    print("1. Register")
    print("2. Login")
    choice = input("Choose 1 or 2: ").strip()
    if choice == '1':
        client_socket.send("REGISTER".encode('utf-8'))
        username = input("Username: ")
        password = input("Password: ")
        client_socket.send(username.encode('utf-8'))
        time.sleep(0.1)
        client_socket.send(password.encode('utf-8'))
        time.sleep(0.1)
        response = client_socket.recv(1024).decode('utf-8')
        print(f"[SERVER]: {response}")
        client_socket.close()
        print(" ^^ Please restart the program to login")
        exit()
    elif choice == '2':
        client_socket.send("LOGIN".encode('utf-8'))
        username = input("Username: ")
        password = input("Password: ")
        client_socket.send(username.encode('utf-8'))
        client_socket.send(password.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        if response == "Login successful!":
            print(f"✅ {response}")
            break
        else:
            print(f"❌ {response}")
            client_socket.close()
            exit()
    else:
        print("Invalid choice! Pleas select 1 or 2 ")
        
try:
    initial_message = client_socket.recv(1024).decode('utf-8')
    print(initial_message)
except:
    pass

def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"\n{message}")
        except:
            print(" Lost connection to server ")
            client_socket.close()
            break

receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

while True:
    try:
        msg = input(f"{username}: ")
        client_socket.send(msg.encode('utf-8'))
    except:
        print(" Cannot send message ")
        client_socket.close()
        break
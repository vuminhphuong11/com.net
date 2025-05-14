import socket
import threading

# Tạo socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))

# Nhập tên người dùng và gửi lên server
username = input("Enter your username: ")
client_socket.send(username.encode('utf-8'))

# Hàm nhận tin nhắn từ server
def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(f"{message}") # In tin nhắn từ server
        except:
            print("Error receiving message.")
            client_socket.close()
            break

# Tạo thread riêng để nhận tin nhắn liên tục
receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True  # Cho phép kết thúc khi đóng chương trình
receive_thread.start()

# Gửi và nhận tin nhắn
while True:
    message = input(f"{username}: ")
    client_socket.send(message.encode('utf-8'))  # Gửi tin nhắn
import socket
import threading

# Khai báo IP và cổng
host = '0.0.0.0'  # Lắng nghe tất cả địa chỉ IP
port = 12345       # Cổng mà server lắng nghe

# Tạo socket TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(5)  # Lắng nghe tối đa 5 kết nối

print(f"[STARTED] Server is listening on {host}:{port}")

# Quản lý danh sách client
clients = []  # Danh sách lưu các client kết nối
usernames = {}  # Mapping socket -> username


def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:  # Đảm bảo không gửi lại cho client đã gửi
            try:
                client.send(message.encode('utf-8'))
            except:
                client.close()
                clients.remove(client)


# Hàm xử lý client
def handle_client(client_socket):
    # Nhận username từ client
    username = client_socket.recv(1024).decode('utf-8')  # Nhận username từ client
    usernames[client_socket] = username
    print(f"[NEW CONNECTION] {username} has connected.")
    
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"[{username}] {message}")
                broadcast(f"[{username}] {message}", client_socket)  # Broadcast tin nhắn đến các client khác
        except:
            clients.remove(client_socket)
            client_socket.close()
            break


# Hàm nhận kết nối từ client và tạo thread cho mỗi client
def receive_connections():
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"[NEW CONNECTION] {client_address} connected.")
        clients.append(client_socket)
        
        # Tạo một thread mới cho mỗi client
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()


# Bắt đầu nhận kết nối từ client
receive_connections()
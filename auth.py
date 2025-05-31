# auth.py
import json
from socket_connection import send_auth_request, reconnect_socket

def register(username, password):
    request = {
        "type": "register",
        "sender": username,
        "content": password
    }
    response = send_auth_request(request)
    
    # Sau khi đăng ký, server đóng socket → cần reconnect
    reconnect_socket()
    return json.loads(response)

def login(username, password):
    request = {
        "type": "login",
        "sender": username,
        "content": password
    }
    response = send_auth_request(request)
    return json.loads(response)

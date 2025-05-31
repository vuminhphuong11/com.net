import tkinter as tk
from tkinter import messagebox
import socket
import protocol
from giao_dien import ChatClientUI 
from register_screen import show_register_screen

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import hashlib

# ==== Mã hóa AES-CBC ====
SECRET_KEY = hashlib.sha256(b'key_dung_de_lam_khoa_32_bits').digest()
BLOCK_SIZE = 16

def pad(data):
    padding_len = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + chr(padding_len) * padding_len

def unpad(data):
    padding_len = ord(data[-1])
    return data[:-padding_len]

def encrypt_message(plain_text):
    iv = get_random_bytes(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    padded = pad(plain_text).encode('utf-8')
    ciphertext = cipher.encrypt(padded)
    return base64.b64encode(iv + ciphertext).decode('utf-8')

def decrypt_message(encoded_data):
    try:
        raw = base64.b64decode(encoded_data)
        iv = raw[:16]
        ciphertext = raw[16:]
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        padded_plain = cipher.decrypt(ciphertext).decode('utf-8')
        return unpad(padded_plain)
    except Exception as e:
        print("Decrypt error:", e)
        return None

# ==== Giao diện đăng nhập ====
class LoginScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Login")
        self.master.configure(bg="#ccf2ff")

        self.frame = tk.Frame(master, bg="#ccf2ff")
        self.frame.pack(padx=50, pady=50)

        tk.Label(self.frame, text="Username:", bg="#ccf2ff").grid(row=0, column=0, sticky="e")
        tk.Label(self.frame, text="Password:", bg="#ccf2ff").grid(row=1, column=0, sticky="e")

        self.username_entry = tk.Entry(self.frame)
        self.username_entry.grid(row=0, column=1)

        self.password_entry = tk.Entry(self.frame, show="*")
        self.password_entry.grid(row=1, column=1)

        self.login_button = tk.Button(self.frame, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.register_link = tk.Button(self.frame, text="Register here", fg="blue", bg="#ccf2ff", cursor="hand2", command=self.goto_register, relief=tk.FLAT)
        self.register_link.grid(row=3, column=0, columnspan=2)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', 12345))

            login_msg = protocol.create_message("login", username, password)
            encrypted_msg = encrypt_message(login_msg)
            msg_bytes = encrypted_msg.encode('utf-8')
            sock.send(len(msg_bytes).to_bytes(4, 'big') + msg_bytes)

            response = self.recv_with_length(sock)
            result = protocol.parse_message(response)

            if result['type'] == 'system' and 'successful' in result['content'].lower():
                messagebox.showinfo("Success", result['content'])
                sock.close()
                self.master.destroy()
                root = tk.Tk()
                app = ChatClientUI(root)
                app.connect(username, password)

                menubar = tk.Menu(root)
                menubar.add_command(label="Members", command=lambda: app.request_members())
                root.config(menu=menubar)

                root.mainloop()
            else:
                messagebox.showerror("Login Failed", result['content'])
            sock.close()

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def recv_with_length(self, sock):
        length_bytes = sock.recv(4)
        if not length_bytes:
            return None
        length = int.from_bytes(length_bytes, 'big')
        encrypted_data = sock.recv(length).decode('utf-8')
        return decrypt_message(encrypted_data)

    def goto_register(self):
        self.master.destroy()
        show_register_screen()

def show_login_screen():
    root = tk.Tk()
    app = LoginScreen(root)
    root.mainloop()

if __name__ == '__main__':
    show_login_screen()

import tkinter as tk
from tkinter import messagebox
import socket
import protocol
from giao_dien import show_main_chat_window

class RegisterScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Register")

        self.frame = tk.Frame(master)
        self.frame.pack(padx=20, pady=20)

        tk.Label(self.frame, text="Username:").grid(row=0, column=0, sticky="e")
        tk.Label(self.frame, text="Password:").grid(row=1, column=0, sticky="e")

        self.username_entry = tk.Entry(self.frame)
        self.username_entry.grid(row=0, column=1)

        self.password_entry = tk.Entry(self.frame, show="*")
        self.password_entry.grid(row=1, column=1)

        self.register_button = tk.Button(self.frame, text="Register", command=self.register)
        self.register_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.back_button = tk.Button(self.frame, text="Back to Login", command=self.back_to_login)
        self.back_button.grid(row=3, column=0, columnspan=2)

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', 12345))

            register_msg = protocol.create_message("register", username, password)
            sock.send(len(register_msg).to_bytes(4, 'big') + register_msg.encode('utf-8'))

            response = self.recv_with_length(sock)
            result = protocol.parse_message(response)

            if result['type'] == 'system' and 'successful' in result['content'].lower():
                messagebox.showinfo("Success", result['content'])
                sock.close()
                self.master.destroy()
                show_main_chat_window(username, password)
            else:
                messagebox.showerror("Register Failed", result['content'])
            sock.close()

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def recv_with_length(self, sock):
        length_bytes = sock.recv(4)
        if not length_bytes:
            return None
        length = int.from_bytes(length_bytes, 'big')
        return sock.recv(length).decode('utf-8')

    def back_to_login(self):
        self.master.destroy()
        from login_screen import show_login_screen
        show_login_screen()


def show_register_screen():
    root = tk.Tk()
    app = RegisterScreen(root)
    root.mainloop()

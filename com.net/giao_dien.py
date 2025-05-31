import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import socket
import threading
import protocol  # Đảm bảo bạn đã có file này
import os
import mimetypes
import base64
from security import encrypt_message, decrypt_message

EMOJI_LIST = ["😄", "😢", "❤️", "👍", "😂", "😍", "😊", "😎", "😭", "😉"]

class ChatClientUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Socket Chat")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = ""

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled', height=20)
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        frame_bottom = tk.Frame(master)
        frame_bottom.pack(fill=tk.X, padx=5, pady=5)

        self.entry_message = tk.Entry(frame_bottom, width=60)
        self.entry_message.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_message.bind("<Return>", self.send_message)

        self.btn_emoji = tk.Button(frame_bottom, text="😊", command=self.toggle_emoji_panel)
        self.btn_emoji.pack(side=tk.LEFT, padx=2)

        self.btn_file = tk.Button(frame_bottom, text="📎", command=self.send_file)
        self.btn_file.pack(side=tk.LEFT, padx=2)

        self.btn_send = tk.Button(frame_bottom, text="Send", command=self.send_message)
        self.btn_send.pack(side=tk.LEFT, padx=2)

        self.emoji_panel = None

    def connect(self, username, password):
        try:
            self.sock.connect(('localhost', 12345))
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            return False

        self.username = username
        msg = protocol.create_message("login", self.username, password)
        send_with_length(self.sock, msg)
        response = recv_with_length(self.sock)
        result = protocol.parse_message(response)
        if result['type'] == 'error':
            messagebox.showerror("Login Failed", result['content'])
            return False

        threading.Thread(target=self.receive_messages, daemon=True).start()
        return True

    def display_message(self, text):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state='disabled')

    def send_message(self, event=None):
        content = self.entry_message.get().strip()
        if not content:
            return
        self.entry_message.delete(0, tk.END)
        msg = protocol.create_message("message", self.username, content)
        send_with_length(self.sock, msg)

    def toggle_emoji_panel(self):
        if self.emoji_panel and self.emoji_panel.winfo_exists():
            self.emoji_panel.destroy()
            self.emoji_panel = None
        else:
            self.emoji_panel = tk.Toplevel(self.master)
            self.emoji_panel.title("Choose Emoji")
            row = 0
            col = 0
            for emoji in EMOJI_LIST:
                btn = tk.Button(self.emoji_panel, text=emoji, width=4, command=lambda e=emoji: self.insert_emoji(e))
                btn.grid(row=row, column=col, padx=2, pady=2)
                col += 1
                if col >= 5:
                    col = 0
                    row += 1

    def insert_emoji(self, emoji):
        self.entry_message.insert(tk.END, emoji)
        if self.emoji_panel:
            self.emoji_panel.destroy()
            self.emoji_panel = None

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            filename = os.path.basename(file_path)
            filetype = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

            msg = protocol.create_file_message(self.username, filename, filetype, file_bytes)
            send_with_length(self.sock, msg)
            self.display_message(f"[You sent file]: {filename}")
        except Exception as e:
            messagebox.showerror("Send File Error", str(e))

    def receive_messages(self):
        while True:
            try:
                msg_json = recv_with_length(self.sock)
                if msg_json is None:
                    break
                msg = protocol.parse_message(msg_json)
                if msg['type'] == 'file':
                    filename = msg['filename']
                    sender = msg['sender']
                    content_b64 = msg['content']
                    file_bytes = base64.b64decode(content_b64)

                    os.makedirs('received_files', exist_ok=True)
                    save_path = os.path.join('received_files', f"{sender}_{filename}")
                    with open(save_path, 'wb') as f:
                        f.write(file_bytes)

                    self.display_message(f"[{sender} sent a file]: {filename} saved to {save_path}")
                else:
                    self.display_message(f"[{msg['sender']}]: {msg['content']}")
            except:
                break
        self.display_message("Disconnected from server.")
        self.sock.close()

    def request_members(self):
        msg = protocol.create_message("message", self.username, "/members")
        send_with_length(self.sock, msg)

def send_with_length(sock, message):
    encrypted = encrypt_message(message)
    msg_bytes = encrypted.encode('utf-8')
    sock.send(len(msg_bytes).to_bytes(4, 'big') + msg_bytes)
def recv_with_length(sock):
    length_bytes = sock.recv(4)
    if not length_bytes:
        return None
    length = int.from_bytes(length_bytes, 'big')
    encrypted_data = sock.recv(length).decode('utf-8')
    return decrypt_message(encrypted_data)

def show_main_chat_window(username, password):
    import tkinter.simpledialog
    root = tk.Tk()
    app = ChatClientUI(root)
    success = app.connect(username, password)
    if success:
        root.mainloop()

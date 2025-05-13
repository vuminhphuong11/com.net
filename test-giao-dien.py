import tkinter as tk

def login():
    username = username_entry.get()
    password = password_entry.get()
    print(f"Logging in as {username} with password {password}")

root = tk.Tk()
root.title("Login")
root.geometry("300x180")

tk.Label(root, text="Username").pack(pady=5)
username_entry = tk.Entry(root)
username_entry.pack()

tk.Label(root, text="Password").pack(pady=5)
password_entry = tk.Entry(root, show="*")
password_entry.pack()

tk.Button(root, text="Login", command=login).pack(pady=10)

root.mainloop()

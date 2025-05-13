import tkinter as tk
from tkinter import messagebox

def show_main_ui():
    main_ui = tk.Toplevel()
    main_ui.title("Main Chat UI")
    main_ui.geometry("300x150")
    tk.Label(main_ui, text="Bạn đã đăng nhập thành công!", font=("Arial", 12)).pack(pady=40)

def handle_login(username_entry, password_entry, window):
    username = username_entry.get()
    password = password_entry.get()
    if username == "group12" and password == "123456":
        window.destroy()
        show_main_ui()
    else:
        messagebox.showerror("Login Failed", "Sai tài khoản hoặc mật khẩu!")

def open_register(window):
    window.destroy()
    import register_screen
    register_screen.show_register()

def show_login():
    window = tk.Tk()
    window.title("Login")
    window.geometry("300x230")

    tk.Label(window, text="Username").pack(pady=5)
    username_entry = tk.Entry(window)
    username_entry.pack()

    tk.Label(window, text="Password").pack(pady=5)
    password_entry = tk.Entry(window, show="*")
    password_entry.pack()

    tk.Button(window, text="Login", command=lambda: handle_login(username_entry, password_entry, window)).pack(pady=10)

    # Dòng chữ đăng ký: in đậm và gạch chân
    register_label = tk.Label(window, text="Register here", fg="blue", cursor="hand2", font=("Arial", 10, "bold", "underline"))
    register_label.pack()
    register_label.bind("<Button-1>", lambda e: open_register(window))

    window.mainloop()

if __name__ == "__main__":
    show_login()
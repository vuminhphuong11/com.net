import tkinter as tk
from tkinter import messagebox

# Danh sách username đã tồn tại (tạm thời)
existing_users = ["group12"]

def show_register():
    def toggle_password(entry, icon_button, is_visible):
        if is_visible[0]:
            entry.config(show="")
            icon_button.config(text="🌙")  
        else:
            entry.config(show="*")
            icon_button.config(text="🌞")
        is_visible[0] = not is_visible[0]

    def handle_register():
        username = username_entry.get()
        password = password_entry.get()
        confirm = confirm_entry.get()

        if username in existing_users:
            messagebox.showerror("Lỗi", "Username đã tồn tại.")
        elif len(username) < 12:
            messagebox.showerror("Lỗi", "Username phải có ít nhất 12 ký tự.")
        elif password != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu không khớp.")
        else:
            existing_users.append(username)
            messagebox.showinfo("Thành công", "Đăng ký thành công!")
            register_window.destroy()
            __import__('main').show_login()

    register_window = tk.Tk()
    register_window.title("Register")
    register_window.geometry("350x300")

    # Nhập username
    tk.Label(register_window, text="Username").pack(pady=5)
    username_entry = tk.Entry(register_window)
    username_entry.pack()

    # Nhập mật khẩu
    tk.Label(register_window, text="Password").pack(pady=5)
    pw_frame = tk.Frame(register_window)
    pw_frame.pack()
    password_entry = tk.Entry(pw_frame, show="*")
    password_entry.pack(side=tk.LEFT)
    pw_visible = [True]
    pw_toggle = tk.Button(pw_frame, text="🌙", command=lambda: toggle_password(password_entry, pw_toggle, pw_visible))
    pw_toggle.pack(side=tk.LEFT)

    # Nhập lại mật khẩu
    tk.Label(register_window, text="Confirm Password").pack(pady=5)
    confirm_frame = tk.Frame(register_window)
    confirm_frame.pack()
    confirm_entry = tk.Entry(confirm_frame, show="*")
    confirm_entry.pack(side=tk.LEFT)
    confirm_visible = [True]
    confirm_toggle = tk.Button(confirm_frame, text="🌙", command=lambda: toggle_password(confirm_entry, confirm_toggle, confirm_visible))
    confirm_toggle.pack(side=tk.LEFT)

    # Nút đăng ký
    tk.Button(register_window, text="Register", command=handle_register).pack(pady=15)

    # Quay lại trang login
    tk.Label(register_window, text="Đã có tài khoản?").pack()
    back_to_login = tk.Button(
        register_window,
        text="Login here",
        command=lambda: [register_window.destroy(), __import__('main').show_login()]
    )
    back_to_login.pack()

    register_window.mainloop()
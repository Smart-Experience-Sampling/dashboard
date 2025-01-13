import pathlib
import tkinter as tk
from tkinter import filedialog, simpledialog
from pocketbase import PocketBase
import pickle


# class App(tk.Tk):
#     def __init__(self):
#         super().__init__()

#         self.title("Smart Experience Sampling Dashboard")
#         self.attributes("-fullscreen", True)

LARGEFONT = ("Verdana", 35)


class App(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, client, *args, **kwargs):

        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Smart Experience Sampling Dashboard")
        # self.attributes("-fullscreen", True)

        self.client = client

        self.login_page()

    def login_page(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.email_label = tk.Label(self, text="Email")
        self.email_label.pack()
        self.email_input = tk.Entry(self)
        self.email_input.pack()

        self.password_label = tk.Label(self, text="Password")
        self.password_label.pack()
        self.password_input = tk.Entry(self)
        self.password_input.pack()

        self.login_button = tk.Button(
            self,
            text="Login",
            command=lambda: self.pb_login(
                self.email_input.get(), self.password_input.get()
            ),
        )
        self.login_button.pack()

    def home_page(self):
        for widget in self.winfo_children():
            widget.destroy()

    def pb_login(self, email, password):
        try:
            user = self.client.collection("users").auth_with_password(email, password)
        except:
            self.error_label = tk.Label(
                self, text="Username and/or password is incorrect"
            )
            self.error_label.pack()
            return
        # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjb2xsZWN0aW9uSWQiOiJfcGJfdXNlcnNfYXV0aF8iLCJleHAiOjE3MzczNzA0MzQsImlkIjoiMmgxa2F1ODJpdzBsYjYzIiwicmVmcmVzaGFibGUiOnRydWUsInR5cGUiOiJhdXRoIn0.Ky8aKoYczEfjaI-m5KfISgckRFDeYdPPwjIKWLvICSg"
        if user.is_valid:
            self.home_page()
            return
        self.error_label = tk.Label(self, text="Username and/or password is incorrect")
        self.error_label.pack()
        # print(user.token)
        user2 = self.client.collection("users").auth_refresh()


if __name__ == "__main__":
    client = PocketBase("http://127.0.0.1:8090")
    app = App(client)
    app.mainloop()

# Check if a data file exists if not show login screen. If it does check the contents and try to use it to login.

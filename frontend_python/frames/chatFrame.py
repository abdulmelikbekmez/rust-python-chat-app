from tkinter import END, Frame, Label, StringVar, Entry, Button
from tkinter.scrolledtext import ScrolledText
from network.listener import Listener


class ChatFrame(Frame):
    def __init__(self, master, name: str, to: str):
        super().__init__(master)
        self.name = name
        self.to = to
        self.label = Label(self, text="Welcome")
        self.label.grid(row=0)

        self.txt = ScrolledText(self, width=60)
        self.txt.grid(row=1, column=0, columnspan=2)
        self.txt.bind("<Key>", lambda _: "break")

        self.msg = StringVar()
        self.e = Entry(self, width=55, textvariable=self.msg)
        self.e.grid(row=2, column=0)

        self.btn_send = Button(self, text="Send", command=self.send)
        self.btn_send.grid(row=2, column=1)

    def insert(self, msg: str):
        self.txt.insert(END, f"{self.to} -> {msg}\n")

    def send(self):
        self.txt.insert(END, f"YOU -> {self.msg.get()}\n")
        Listener.send_direct_message(self.name, self.to, self.msg.get())
        self.msg.set("")

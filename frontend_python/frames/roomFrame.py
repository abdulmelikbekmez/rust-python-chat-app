from tkinter import END, Frame, Label, StringVar, Entry, Button, Text, filedialog as f
from tkinter.scrolledtext import ScrolledText
from emoji import emojize

from network.listener import Listener


class RoomFrame(Frame):
    def __init__(self, master, owner: str, client: str):
        super().__init__(master)
        self.owner = owner
        self.client = client
        self.label = Label(self, text="Welcome")
        self.label.grid(row=0)

        self.tmp = StringVar()
        self.txt = ScrolledText(self, width=60)
        self.txt.bind("<Key>", lambda _: "break")
        self.txt.grid(row=1, column=0, columnspan=2)

        self.msg = StringVar()
        self.e = Entry(self, width=55, textvariable=self.msg)
        self.e.grid(row=2, column=0)

        self.btn_send = Button(self, text="Send", command=self.send)
        self.btn_send.grid(row=2, column=1)

        self.btn_file = Button(self, text="send file", command=self.send_file)
        self.btn_file.grid(row=2, column=2)

    def send_file(self):
        filetypes = (
            ("text files", "*.txt"),
            ("pdf files", "*.pdf"),
            ("jpg files", "*.jpg"),
        )
        filename = f.askopenfilename(title="open file", filetypes=filetypes)
        if not filename:
            return
        with open(filename, "rb") as fi:
            readed = fi.read()
            Listener.send_file(self.client, self.owner, filename, readed)

    def insert(self, _from: str, msg: str):
        self.txt.insert(END, f"{_from} -> {msg}\n")

    def send(self):
        self.insert("YOU", self.msg.get())
        Listener.send_room_message(self.client, self.owner, self.msg.get())
        self.msg.set("")

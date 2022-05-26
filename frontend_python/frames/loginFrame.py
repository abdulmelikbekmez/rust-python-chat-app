import tkinter as tk
from tkinter import Button, Entry, IntVar, Label, Spinbox, StringVar, ttk
from tkinter.constants import DISABLED, NORMAL

from frames.mainFrame import MainFrame
from network.listener import Listener
from network.sharedState import SharedState


class LoginFrame(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.geometry("800x600")
        self.title("Chat App")

        self.name = StringVar()
        self.frame_name = NameFrame(self.name, self)
        self.frame_name.pack(fill="x")

        self.address = StringVar(value="localhost")
        self.frame_address = AddressFrame(self.address, self)
        self.frame_address.pack(fill="x")

        self.port = IntVar(value=8000)
        self.frame_port = PortFrame(self.port, self)
        self.frame_port.pack(fill="x")

        self.btn_connect = Button(
            self, text="Connect", command=self.on_connect, state=DISABLED
        )
        self.btn_connect.pack()

        self.connected = False

    def is_connection_valid(self):

        return (
            not self.connected
            and len(self.name.get()) > 1
            and len(self.address.get()) > 3
        )

    def on_connect(self):
        address = self.frame_address.get_address()
        name = self.frame_name.get_name()
        port = self.frame_port.get_port()

        state = SharedState(address, port, name)
        listener = Listener(state)
        listener.start()

        self.destroy()
        main_frame = MainFrame(state.name)
        listener.set_frame(main_frame)
        if listener.is_alive():
            main_frame.mainloop()


class NameFrame(ttk.Frame):
    def __init__(self, name: StringVar, main: LoginFrame):
        super().__init__(main)
        self.main = main
        self.lbl_name = Label(self, text="name")
        self.lbl_name.pack(side="left")

        self.name = name
        self.entry_name = Entry(self, bd=5, textvariable=self.name)
        self.entry_name.pack(side="right")
        self.entry_name.bind("<KeyRelease>", self.is_valid)

    def is_valid(self, event):
        if not self.main.is_connection_valid():
            self.main.btn_connect["state"] = DISABLED
        else:
            self.main.btn_connect["state"] = NORMAL

    def get_name(self):
        return self.entry_name.get()


class AddressFrame(ttk.Frame):
    def __init__(self, address: StringVar, main):
        super().__init__(main)
        self.lbl_address = Label(self, text="Ip Address")
        self.lbl_address.pack(side="left")

        self.address = address

        self.entry_address = Entry(self, bd=5, textvariable=self.address)
        self.entry_address.pack(side="right")

    def get_address(self):
        return self.address.get()


class PortFrame(ttk.Frame):
    def __init__(self, port: IntVar, main):
        super().__init__(main)
        self.lbl_port = Label(self, text="Port")
        self.lbl_port.pack(side="left")

        self.port = port

        self.spn_port = Spinbox(self, from_=1025, to=65535, textvariable=self.port)
        self.spn_port.pack(side="right")

    def get_port(self):
        return self.port.get()

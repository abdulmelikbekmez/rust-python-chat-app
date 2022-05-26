from tkinter import Button, Frame, ttk
import tkinter as tk
from frames.chatFrame import ChatFrame
from frames.roomFrame import RoomFrame
from network.listener import Listener
from tkinter.simpledialog import askstring


class MainFrame(tk.Tk):
    def __init__(self, name: str):
        super().__init__()
        self.active = True
        self.geometry("800x600")
        self.name = name
        self.title(f"Hello {self.name}")

        self.dict_client: dict[str, ChatFrame] = {}
        self.dict_rooms: dict[str, RoomFrame] = {}

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, expand=True)

        self.frm_main = Frame(self.notebook)
        self.notebook.add(self.frm_main, text=f"Hello {self.name}")

        self.frame_tree = Frame(self.frm_main)
        self.frame_tree.pack()

        self.cols_tree_clients = "Clients"
        self.tree_clients = ttk.Treeview(
            self.frame_tree, columns=self.cols_tree_clients, show="headings"
        )
        self.tree_clients.pack(side="left")
        self.tree_clients.heading(self.cols_tree_clients, text=self.cols_tree_clients)
        self.tree_clients.bind("<<TreeviewSelect>>", self.__client_selected)

        # ---------------------------------
        self.cols_tree_rooms = ("Room Name", "Owner", "Guest Number")
        self.tree_rooms = ttk.Treeview(
            self.frame_tree, columns=self.cols_tree_rooms, show="headings"
        )
        self.tree_rooms.pack(side="right")
        for col in self.cols_tree_rooms:
            self.tree_rooms.heading(col, text=col)
        self.tree_rooms.bind("<<TreeviewSelect>>", self.__room_selected)

        self.btn = Button(self.frm_main, text="create room", command=self.__create_room)
        self.btn.pack()

    def __del__(self):
        self.active = False

    def __create_room(self):
        room_name = askstring("Enter Room Name", "Please enter room name to create")
        if not room_name:
            return
        Listener.send_create_room(self.name, room_name)

    def __clear_clients(self):
        for i in self.tree_clients.get_children():
            self.tree_clients.delete(i)

    def __clear_rooms(self):
        for i in self.tree_rooms.get_children():
            self.tree_rooms.delete(i)

    def __clear_room_notebooks(self):
        # TODO:
        pass

    def add_chat_notebook(self, to: str):
        if self.dict_client.get(to):
            return
        c = ChatFrame(self.notebook, self.name, to)
        self.dict_client[to] = c
        self.notebook.add(c, text=f"{to} private message")

    def __client_selected(self, event):
        for selected in self.tree_clients.selection():
            item = self.tree_clients.item(selected)
            client = item["values"][0]

            if (
                not isinstance(client, str)
                or self.name == client
                or self.dict_client.get(client)
            ):
                continue

            self.add_chat_notebook(client)

    def __room_selected(self, event):
        for selected in self.tree_rooms.selection():
            item = self.tree_rooms.item(selected)
            room_name = item["values"][0]
            owner = item["values"][1]

            if self.dict_rooms.get(owner) or self.name == owner:
                continue

            Listener.send_join_room(owner)

    def update_clients(self, data: list[str]):
        self.__clear_clients()
        for d in data:
            self.tree_clients.insert("", "end", values=[d])

        l = [
            (client, frame)
            for client, frame in self.dict_client.items()
            if client not in data
        ]

        for client, frame in l:
            self.notebook.forget(frame)
            del self.dict_client[client]

    def update_rooms(self, data: list[dict]):
        self.__clear_rooms()
        owner_list = []
        for room in data:
            owner_list.append(room["owner"])
            self.tree_rooms.insert(
                "", "end", values=[room["name"], room["owner"], len(room["guests"])]
            )
            if (
                self.name in room["guests"] or self.name == room["owner"]
            ) and not self.dict_rooms.get(room["owner"]):
                c = RoomFrame(self.notebook, room["owner"], self.name)
                self.dict_rooms[room["owner"]] = c
                self.notebook.add(c, text=f"{room['name']} Room")

        l = [
            (owner, frame)
            for owner, frame in self.dict_rooms.items()
            if owner not in owner_list
        ]
        for owner, frame in l:
            self.notebook.forget(frame)
            del self.dict_rooms[owner]

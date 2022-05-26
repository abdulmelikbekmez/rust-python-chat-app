from __future__ import annotations
import json
import os
from os.path import exists
from socket import AF_INET, SOCK_STREAM, socket
import sys
from threading import Thread
from time import sleep
from tkinter.messagebox import showerror

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from frames.mainFrame import MainFrame

from network.sharedState import SharedState


class Listener(Thread):
    sock: socket | None = None

    def __init__(self, shared_state: SharedState):
        super().__init__()
        self.daemon = True
        self.state = shared_state
        self.frame = None

    def set_frame(self, frame: MainFrame):
        self.frame = frame

    @classmethod
    def send_file(cls, _from: str, room: str, filename: str, byte: bytes):
        if not cls.sock:
            return

        req = {
            "type": "SendFile",
            "content": {
                "from": _from,
                "room": room,
                "filename": os.path.splitext(filename)[1],
                "size": len(byte),
            },
        }

        req = json.dumps(req)
        print(f"size of request => {len(req)}")
        print(f"size of file => {len(byte)}")
        cls.sock.sendall(bytes(req, encoding="utf-8"))
        sleep(0.5)
        cls.sock.sendall(byte)

    @classmethod
    def send_join_room(cls, room_owner: str):
        if not cls.sock:
            return
        req = {
            "type": "JoinRoom",
            "content": {"room": room_owner},
        }
        req = json.dumps(req)
        cls.sock.sendall(bytes(req, encoding="utf-8"))

    @classmethod
    def send_direct_message(cls, _from: str, to: str, msg: str):
        if not cls.sock:
            return
        req = {
            "type": "DirectMessage",
            "content": {"from": _from, "to": to, "message": msg},
        }
        req = json.dumps(req)
        cls.sock.sendall(bytes(req, encoding="utf-8"))

    @classmethod
    def send_room_message(cls, _from: str, room: str, msg: str):
        if not cls.sock:
            return

        req = {
            "type": "RoomMessage",
            "content": {"from": _from, "room": room, "message": msg},
        }
        req = json.dumps(req)
        print(f"\n{req} sended\n")
        cls.sock.sendall(bytes(req, encoding="utf-8"))

    @classmethod
    def send_create_room(cls, owner: str, room_name: str):
        if not cls.sock:
            return

        req = {
            "type": "CreateRoom",
            "content": {"owner": owner, "name": room_name},
        }
        req = json.dumps(req)
        cls.sock.sendall(bytes(req, encoding="utf-8"))

    def __del__(self):
        while not self.frame:
            sleep(0.1)

        if self.frame.active:
            self.frame.destroy()

    def on_update(self, obj):
        while not self.frame:
            sleep(0.1)
            print("sleeping")
        self.frame.update_clients(obj["clients"])

    def on_update_rooms(self, obj):
        while not self.frame:
            sleep(0.1)
            print("sleeping")
        self.frame.update_rooms(obj["rooms"])

    def on_update_all(self, obj):
        while not self.frame:
            sleep(0.1)
        self.frame.update_clients(obj["clients"])
        self.frame.update_rooms(obj["rooms"])

    def on_direct_message(self, _from: str, msg: str):
        while not self.frame:
            sleep(0.1)
        if not self.frame.dict_client.get(_from):
            self.frame.add_chat_notebook(_from)

        self.frame.dict_client[_from].insert(msg)

    def on_room_message(self, _from: str, room: str, msg: str):
        while not self.frame:
            sleep(0.1)
        self.frame.dict_rooms[room].insert(_from, msg)

    def on_send_file(self, _from: str, room: str, filename: str, size: int):
        if not self.sock:
            return
        print("\n Dosya Okuma basliyooorr!! \n ")
        max_size = 256 * 256
        num = 0
        while exists(f"downloaded-{num}{filename}"):
            num += 1
        with open(f"downloaded-{num}{filename}", "wb") as f:
            while size > 0:
                buf = self.sock.recv(max_size)
                size -= len(buf)
                f.write(buf)

    def run(self):

        req = {"type": "Introduce", "content": {"name": self.state.name}}
        req = json.dumps(req)

        with socket(AF_INET, SOCK_STREAM) as s:
            try:
                s.connect((self.state.ip_address, self.state.port))
            except ConnectionError as e:
                print(e)
                print("Aborting the program...")
                sys.exit()
            s.sendall(bytes(req, encoding="utf-8"))
            Listener.sock = s

            while True:
                data = s.recv(1024)
                if not data:
                    break

                print(f"\nreceived byte {data}\n")
                data = json.loads(data)
                print(f"\nreceived json {data}\n")

                match data:
                    case {"type": "Update", "content": obj}:
                        self.on_update(obj)

                    case {"type": "UpdateRooms", "content": obj}:
                        self.on_update_rooms(obj)

                    case {"type": "UpdateAll", "content": obj}:
                        self.on_update_all(obj)

                    case {
                        "type": "DirectMessage",
                        "content": {"from": _from, "message": msg},
                    }:
                        self.on_direct_message(_from, msg)

                    case {
                        "type": "RoomMessage",
                        "content": {"from": _from, "room": room, "message": msg},
                    }:
                        self.on_room_message(_from, room, msg)

                    case {
                        "type": "SendFile",
                        "content": {
                            "from": _from,
                            "room": room,
                            "filename": filename,
                            "size": size,
                        },
                    }:
                        self.on_send_file(_from, room, filename, size)

                    case {"type": "Warning", "content": obj}:
                        showerror(message=obj["message"])

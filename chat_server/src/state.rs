use std::sync::{Arc, Mutex};

use tokio::{
    io::{AsyncWriteExt, BufReader},
    net::tcp::{ReadHalf, WriteHalf},
    sync::broadcast::{Receiver, Sender},
};

use crate::{message::Message, response::Response, room::Room};

pub type SharedRooms = Arc<Mutex<Vec<Room>>>;
pub type SharedClients = Arc<Mutex<Vec<String>>>;

pub struct State<'a> {
    pub name: String,
    pub reader: BufReader<ReadHalf<'a>>,
    pub writer: WriteHalf<'a>,
    pub tx: Sender<Message>,
    pub rx: Receiver<Message>,
    pub clients: Arc<Mutex<Vec<String>>>,
    pub rooms: Arc<Mutex<Vec<Room>>>,
    pub buffer: [u8; 1024],
}

impl<'a> State<'a> {
    fn copy_clients(&mut self) -> Vec<String> {
        self.clients.lock().unwrap().clone()
    }

    fn copy_rooms(&mut self) -> Vec<Room> {
        self.rooms.lock().unwrap().clone()
    }

    async fn send_response(&mut self, response: &Response) {
        let buff = serde_json::to_vec::<Response>(&response).unwrap();
        self.writer.write_all(buff.as_slice()).await.unwrap();
    }

    pub fn new(
        reader: BufReader<ReadHalf<'a>>,
        writer: WriteHalf<'a>,
        tx: Sender<Message>,
        clients: SharedClients,
        rooms: SharedRooms,
    ) -> Self {
        let rx = tx.subscribe();
        Self {
            name: String::new(),
            tx,
            rx,
            clients,
            rooms,
            buffer: [0; 1024],
            reader,
            writer,
        }
    }

    pub async fn send_response_update(&mut self) {
        let response = Response::Update {
            clients: self.copy_clients(),
        };
        self.send_response(&response).await
    }

    pub async fn send_response_update_rooms(&mut self) {
        let response = Response::UpdateRooms {
            rooms: self.copy_rooms(),
        };
        self.send_response(&response).await
    }

    pub async fn send_response_update_all(&mut self) {
        let response = Response::UpdateAll {
            clients: self.copy_clients(),
            rooms: self.copy_rooms(),
        };
        self.send_response(&response).await
    }

    pub async fn send_response_warning(&mut self, message: String) {
        let response = Response::Warning { message };
        self.send_response(&response).await
    }

    pub async fn send_response_direct_message(&mut self, from: String, message: String) {
        let response = Response::DirectMessage { from, message };
        self.send_response(&response).await
    }

    pub async fn send_response_room_message(
        &mut self,
        from: String,
        room: String,
        message: String,
    ) {
        let response = Response::RoomMessage {
            from,
            room,
            message,
        };
        self.send_response(&response).await
    }

    pub async fn send_response_file(
        &mut self,
        from: String,
        room: String,
        filename: String,
        data: &Vec<u8>,
    ) {
        let response = Response::SendFile {
            from,
            room,
            filename,
            size: data.len(),
        };
        self.send_response(&response).await;
    }

    pub async fn send_message_update(&self) {
        self.tx
            .send(Message::Update {
                from: self.name.clone(),
            })
            .unwrap();
    }

    pub async fn send_message_update_rooms(&self) {
        self.tx
            .send(Message::UpdateRoom {
                from: self.name.clone(),
            })
            .unwrap();
    }

    pub async fn send_message_update_all(&self) {
        self.tx
            .send(Message::UpdateAll {
                from: self.name.clone(),
            })
            .unwrap();
    }

    pub async fn send_message_direct_message(&self, to: String, message: String) {
        self.tx
            .send(Message::DirectMessage {
                from: self.name.clone(),
                to,
                message,
            })
            .unwrap();
    }

    pub async fn send_message_room_message(&self, from: String, room: String, message: String) {
        self.tx
            .send(Message::RoomMessage {
                from,
                room,
                message,
            })
            .unwrap();
    }

    pub async fn send_message_file(
        &self,
        from: String,
        room: String,
        filename: String,
        data: Vec<u8>,
    ) {
        self.tx
            .send(Message::SendFile {
                from,
                room,
                filename,
                data,
            })
            .unwrap();
    }

    pub fn remove_client(&mut self) {
        self.clients.lock().unwrap().retain(|x| x != &self.name);
    }

    pub fn is_room_exist(&self, owner: &String) -> bool {
        self.rooms.lock().unwrap().iter().any(|x| x.owner == *owner)
    }

    pub fn has_own_room(&self) -> bool {
        self.rooms
            .lock()
            .unwrap()
            .iter()
            .any(|x| x.owner == self.name)
    }

    pub fn is_in_room(&self, owner_of_room: &String) -> bool {
        self.rooms
            .lock()
            .unwrap()
            .iter()
            .any(|x| x.owner == *owner_of_room && x.guests.iter().any(|guest| *guest == self.name))
    }

    pub fn is_in_any_room(&self) -> bool {
        self.rooms
            .lock()
            .unwrap()
            .iter()
            .any(|x| x.guests.iter().any(|guest| *guest == self.name))
    }

    pub fn join_room(&mut self, room: String) {
        for r in self.rooms.lock().unwrap().iter_mut() {
            if r.owner == room {
                r.guests.push(self.name.clone());
            }
        }
    }

    pub fn leave_room(&mut self) {
        for i in self.rooms.lock().unwrap().iter_mut() {
            i.guests.retain(|guest| *guest != self.name)
        }
    }

    pub fn add_room(&mut self, owner: String, name: String) {
        let guests: Vec<String> = Vec::new();
        self.rooms.lock().unwrap().push(Room {
            owner,
            name,
            guests,
        });
    }

    pub fn delete_room(&mut self) {
        self.rooms.lock().unwrap().retain(|x| x.owner != self.name)
    }
}

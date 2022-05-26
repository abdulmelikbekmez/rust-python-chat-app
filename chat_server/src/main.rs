pub mod message;
pub mod request;
pub mod response;
pub mod room;
pub mod state;

use std::{
    io::Error,
    sync::{Arc, Mutex},
    time::Duration,
};

use tokio::{
    io::{AsyncReadExt, AsyncWriteExt, BufReader},
    net::{TcpListener, TcpStream},
    sync::broadcast::{self, error::RecvError, Sender},
    time::sleep,
};

use crate::{
    message::Message,
    request::Request,
    state::{SharedClients, SharedRooms, State},
};

const IP_ADDR: &str = "127.0.0.1";
const PORT: u16 = 8000;

#[tokio::main]
async fn main() {
    let listener = TcpListener::bind(format!("{}:{}", IP_ADDR, PORT))
        .await
        .unwrap();
    println!("server listening on port {}", PORT);

    let clients: SharedClients = Arc::new(Mutex::new(Vec::new()));
    let rooms: SharedRooms = Arc::new(Mutex::new(Vec::new()));

    let (tx, _) = broadcast::channel::<Message>(30);

    loop {
        let (socket, _addr) = listener.accept().await.unwrap();

        let tx = tx.clone();
        let clients = clients.clone();
        let rooms = rooms.clone();

        tokio::spawn(async { handle_client(socket, tx, clients, rooms).await });
    }
}

async fn handle_client(
    mut socket: TcpStream,
    tx: Sender<Message>,
    clients: SharedClients,
    rooms: SharedRooms,
) {
    let (read, write) = socket.split();
    let reader = BufReader::new(read);
    let mut state = State::new(reader, write, tx, clients, rooms);
    println!("new connection established");

    match introduce(&mut state).await {
        Ok(name) => {
            state.name.push_str(name.as_str());
            state.clients.lock().unwrap().push(state.name.clone());

            state.send_message_update().await;
            state.send_response_update_all().await;
        }
        Err(e) => {
            println!("{}", e);
            return;
        }
    }

    println!("client name => {}", state.name);

    loop {
        tokio::select! {
            result = state.reader.read(&mut state.buffer) => {
                if !on_socket_read(result,&mut state).await {
                    break;
                };
            }

            result = state.rx.recv() => {
                on_received(result, &mut state).await;

            }
        }
    }
}

async fn introduce<'a>(state: &mut State<'a>) -> Result<String, String> {
    match state.reader.read(&mut state.buffer).await {
        Ok(0) => Err("Connection Closed duo to 0 byte readed".to_string()),
        Ok(size) => {
            let deser = Request::from_slice(&state.buffer, size);
            return match deser {
                Request::Introduce { name } => Ok(name),
                _ => Err("wrong type".to_string()),
            };
        }
        Err(e) => Err(e.to_string()),
    }
}

async fn on_socket_read<'a>(result: Result<usize, Error>, state: &mut State<'a>) -> bool {
    match result {
        Ok(0) => {
            println!("connection closed");
            state.remove_client();
            state.leave_room();
            if state.has_own_room() {
                state.delete_room();
            }
            state.send_message_update_all().await;
            false
        }
        Ok(size) => {
            println!("received byte size => {}", size);
            let deser = Request::from_slice(&state.buffer, size);
            match deser {
                Request::Introduce { name } => {
                    println!("name {} already introduces!! \n Closing connection..", name);
                    return false;
                }
                Request::DirectMessage {
                    to,
                    message,
                    from: _,
                } => state.send_message_direct_message(to, message).await,
                Request::CreateRoom { owner, name } => {
                    println!("{} wants to create room", owner);
                    if !state.is_room_exist(&owner) {
                        state.add_room(owner, name);
                        state.send_response_update_rooms().await;
                        state.send_message_update_rooms().await;
                    } else {
                        state
                            .send_response_warning(String::from("Room already exist!!"))
                            .await;
                    }
                }
                Request::JoinRoom { room } => {
                    if state.name == room {
                        state
                            .send_response_warning(String::from("You own that room"))
                            .await;
                    } else if state.is_in_room(&room) {
                        state
                            .send_response_warning(String::from(" You are already in that room"))
                            .await;
                    } else {
                        state.join_room(room);
                        state.send_response_update_rooms().await;
                        state.send_message_update_rooms().await;
                    }
                }
                Request::RoomMessage {
                    from,
                    room,
                    message,
                } => state.send_message_room_message(from, room, message).await,
                Request::SendFile {
                    from,
                    room,
                    filename,
                    size,
                } => {
                    println!("file request, waiting for another request!!");
                    let mut buffer = vec![0; size];
                    if let Ok(size) = state.reader.read_exact(&mut buffer).await {
                        println!("file readed with buffer size {}", size);
                        state.send_message_file(from, room, filename, buffer).await;
                    } else {
                        println!("error occured on reading file");
                        return false;
                    }
                }
            }
            true
        }
        Err(_) => {
            println!("error occured, closing connection");
            false
        }
    }
}

async fn on_received<'a>(result: Result<Message, RecvError>, state: &mut State<'a>) {
    match result {
        Ok(msg) => match msg {
            Message::Update { from } => {
                if from != state.name {
                    state.send_response_update().await;
                }
            }
            Message::UpdateRoom { from } => {
                if from != state.name {
                    state.send_response_update_rooms().await;
                }
            }
            Message::UpdateAll { from } => {
                if from != state.name {
                    state.send_response_update_all().await;
                }
            }
            Message::DirectMessage { from, to, message } => {
                if from != state.name && to == state.name {
                    state.send_response_direct_message(from, message).await;
                }
            }
            Message::RoomMessage {
                from,
                room,
                message,
            } => {
                if from != state.name && (room == state.name || state.is_in_room(&room)) {
                    state.send_response_room_message(from, room, message).await;
                }
            }
            Message::SendFile {
                from,
                room,
                filename,
                data,
            } => {
                if from != state.name && (room == state.name || state.is_in_room(&room)) {
                    state.send_response_file(from, room, filename, &data).await;
                    // TODO: refactor !! think about sleep
                    sleep(Duration::from_secs_f32(2.0)).await;
                    state.writer.write_all(&data).await.unwrap()
                }
            }
        },
        Err(_) => todo!(),
    }
}

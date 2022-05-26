use serde::Serialize;

use crate::room::Room;

#[derive(Serialize)]
#[serde(tag = "type", content = "content")]
pub enum Response {
    Update {
        clients: Vec<String>,
    },
    UpdateRooms {
        rooms: Vec<Room>,
    },
    UpdateAll {
        clients: Vec<String>,
        rooms: Vec<Room>,
    },
    Warning {
        message: String,
    },
    DirectMessage {
        from: String,
        message: String,
    },
    RoomMessage {
        from: String,
        room: String,
        message: String,
    },
    SendFile {
        from: String,
        room: String,
        filename: String,
        size: usize,
    },
}

impl Response {}

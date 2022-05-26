use serde::Deserialize;

#[derive(Deserialize, Debug)]
#[serde(tag = "type", content = "content")]
pub enum Request {
    Introduce {
        name: String,
    },
    CreateRoom {
        owner: String,
        name: String,
    },
    JoinRoom {
        room: String,
    },
    DirectMessage {
        from: String,
        to: String,
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

impl Request {
    pub fn from_slice(data: &[u8], size: usize) -> Self {
        serde_json::from_slice::<Request>(&data[..size]).unwrap()
    }

    pub fn from_vec(data: &Vec<u8>, size: usize) -> Self {
        serde_json::from_slice::<Request>(&data.as_slice()[..size]).unwrap()
    }
}

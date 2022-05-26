#[derive(Debug, Clone)]
pub enum Message {
    Update {
        from: String,
    },
    UpdateRoom {
        from: String,
    },
    UpdateAll {
        from: String,
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
        data: Vec<u8>,
    },
}

impl Message {}

use serde::Serialize;

#[derive(Serialize, Clone)]
pub struct Room {
    pub owner: String,
    pub name: String,
    pub guests: Vec<String>,
}

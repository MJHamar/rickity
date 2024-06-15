use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};  // You need to add `chrono` to your Cargo.toml too
use log::debug;

pub const HABITS_KEY: &str = "habits";
pub const HABITS_CHECK_KEY: &str = "habits_check";

// a dictionary with a single key-value pair: "status": "ok"
#[derive(Serialize, Deserialize)]
pub struct DefaultResponse {
    pub status: String
}
impl Default for DefaultResponse {
    fn default() -> Self {
        DefaultResponse {
            status: "ok".to_string()
        }
    }
}


#[derive(Serialize, Deserialize)]
pub struct Habit {
    pub id: String,
    pub name: String,
    pub description: String,
    pub create_dt: DateTime<Utc>,
    pub frequency: String,
}

#[derive(Serialize, Deserialize)]
pub struct NewHabit {
    pub name: String,
    pub description: String,
    pub frequency: String,
}

#[derive(Serialize, Deserialize)]
pub struct HabitCheckList {
    pub id: String,
    #[serde(with = "crate::util::datetime_util")]
    pub check_dt: Vec<DateTime<Utc>>,
}

pub async fn test_redis() -> redis::RedisResult<()> {
    let client = redis::Client::open("redis://127.0.0.1/")?;
    let mut con = client.get_multiplexed_async_connection().await?;
    
    // Set a key
    let _: () = con.set("test_key", "test_value").await?;
    
    // Get a key
    let result: String = con.get("test_key").await?;
    assert_eq!(result, "test_value");

    // Delete the key and test if the number of keys deleted was 1
    let result: i32 = con.del("test_key").await?;
    assert_eq!(result, 1);

    debug!("Redis test OK");

    Ok(())
}

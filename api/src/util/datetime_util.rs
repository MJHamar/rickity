use serde::{Deserialize, Deserializer, Serialize, Serializer};
use chrono::{DateTime, TimeZone, Utc};

pub fn serialize<S>(dates: &Vec<DateTime<Utc>>, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let timestamps: Vec<i64> = dates.iter().map(|dt| dt.timestamp()).collect();
    timestamps.serialize(serializer)
}

pub fn deserialize<'de, D>(deserializer: D) -> Result<Vec<DateTime<Utc>>, D::Error>
where
    D: Deserializer<'de>,
{
    let timestamps: Vec<i64> = Vec::deserialize(deserializer)?;
    let dates: Vec<DateTime<Utc>> = timestamps
        .into_iter()
        .map(|ts| Utc.from_utc_datetime(&chrono::NaiveDateTime::from_timestamp(ts, 0)))
        .collect();
    Ok(dates)
}
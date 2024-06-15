use config::{ConfigBuilder, File, builder::DefaultState, FileFormat};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Settings {
    pub api: Api,
    pub redis: Redis,
}

#[derive(Debug, Deserialize)]
pub struct Api {
    pub host: String,
    pub port: u16,
    pub loglevel: String,
}

#[derive(Debug, Deserialize)]
pub struct Redis {
    pub host: String,
    pub port: u16,
    pub loglevel: String,
}

pub fn load_config() -> Settings {
    let config = ConfigBuilder::<DefaultState>::default()
    .add_source(File::new("config.ini", FileFormat::Ini))
    .build().expect("Could not build config");

    let api_config = config.get_table("api").unwrap();

    let api = Api {
        host: api_config.get("host").unwrap().to_string(),
        port: api_config.get("port").unwrap().to_string().parse::<u16>().unwrap(),
        loglevel: api_config.get("loglevel").unwrap().to_string(),
    };
    let redis_config = config.get_table("redis").unwrap();

    let redis = Redis {
        host: redis_config.get("host").unwrap().to_string(),
        port: redis_config.get("port").unwrap().to_string().parse::<u16>().unwrap(),
        loglevel: redis_config.get("loglevel").unwrap().to_string(),
    };
    let settings = Settings {
        api,
        redis,
    };
    settings
}

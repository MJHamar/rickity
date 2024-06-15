// mod api;
// mod db_conn;
// mod habits;

use simple_logger::{SimpleLogger, set_up_color_terminal};
use api::util::settings::load_config;

fn main() {
    set_up_color_terminal();
    let settings = load_config();

    let logger = SimpleLogger::new();
    // set loglevel based on config api/loglevel attribute
    let loglevel: String = settings.api.loglevel;
    let max_level = match loglevel.as_str() {
            "error" => log::LevelFilter::Error,
            "warn" => log::LevelFilter::Warn,
            "info" => log::LevelFilter::Info,
            "debug" => log::LevelFilter::Debug,
            "trace" => log::LevelFilter::Trace,
            _ => log::LevelFilter::Info,
        };
    log::set_max_level(max_level);
    log::set_boxed_logger(Box::new(logger)).unwrap();
    log::info!("Log level is set to: {:?}", loglevel);

    api::api::serve().unwrap();
}
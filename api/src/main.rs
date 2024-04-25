// mod api;
// mod db_conn;
// mod habits;

use simple_logger::{SimpleLogger, set_up_color_terminal};

fn main() {
    set_up_color_terminal();
    
    let logger = SimpleLogger::new();
    let max_level = log::Level::Debug.to_level_filter();
    log::set_max_level(max_level);
    log::set_boxed_logger(Box::new(logger)).unwrap();

    api::api::serve().unwrap();
}
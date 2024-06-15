use actix_web::web::Data;
use actix_web::{web, App, HttpServer, Responder};
use actix_cors::Cors;
use log::{info, debug, error};
use crate::db_conn;
use crate::habits;
use crate::util::settings::load_config;

async fn index() -> impl Responder {
    "Hello! This is the habit tracker backend. You should leave..."
}

#[actix_web::main]
pub async fn serve() -> std::io::Result<()> {
    info!("Starting server ...");
    let settings = load_config();

    // Set up redis connection
    let redis_params: String = format!("redis://{}:{}", settings.redis.host, settings.redis.port);
    match db_conn::test_redis(redis_params.clone()).await {
        Ok(_) => debug!("Redis connection successful"),
        Err(e) => error!("Error connecting to Redis: {}", e),
    }
    let redis = redis::Client::open(redis_params).unwrap();

    // Set up server
    let server_url = format!("{}:{}", settings.api.host, settings.api.port);

    HttpServer::new(move || {
        let cors: Cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header();
        App::new()
            .wrap(cors)
            .app_data(Data::new(redis.clone()))
            .route("/", web::get().to(index))
            .route("/habits", web::get().to(habits::get_habits))
            .route("/habits", web::post().to(habits::create_habit))
            .route("/habits/{id}", web::get().to(habits::get_habit))
            .route("/habits/{id}", web::delete().to(habits::delete_habit))
            .route("/habits/{id}/check", web::post().to(habits::check_habit))
            .route("/habits/{id}/check", web::get().to(habits::list_habit_checks))
    })
    .bind(server_url)?
    .run()
    .await
}

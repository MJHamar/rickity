// Integration tests for the habits endpoints
// Run with `cargo test --test test_habits_endpoints`
//
// This test module uses the `actix_web::test` module to test the habits endpoints.
// The `setup_redis` function initializes a Redis connection for testing.
// The `test_get_habits` function tests the `GET /habits` endpoint.
// The `test_create_habit` function tests the `POST /habit` endpoint.
// The `test_check_habit` function tests the `POST /habit/{id}/check` endpoint.
//
// The `test_get_habit` and `test_delete_habit` functions are not implemented.
// You can implement them as an exercise.

extern crate api;

use actix_web::web::Bytes;
use api::db_conn::{Habit, NewHabit, HabitCheckList, DefaultResponse};
use api::habits::*;
use redis::Client;
use actix_web::{test, web, App};

// Initialize Redis connection for testing
async fn setup_redis() -> Client {
    let client = Client::open("redis://127.0.0.1/").unwrap();
    client
}

#[actix_rt::test]
async fn test_get_habits() {
    let client = setup_redis().await;
    let mut app = test::init_service(
        App::new()
            .app_data(client.clone())
            .route("/habits", web::get().to(get_habits)),
    )
    .await;

    let req = test::TestRequest::get().uri("/habits").to_request();
    let resp: Vec<Habit> = test::call_and_read_body_json(&mut app, req).await;

    assert!(resp.is_empty(), "Expected no habits initially");
}

#[actix_rt::test]
async fn test_create_habit() {
    let client = setup_redis().await;
    let mut app = test::init_service(
        App::new()
            .app_data(client.clone())
            .route("/habit", web::post().to(create_habit)),
    )
    .await;

    let new_habit = NewHabit {
        name: "Read a book".to_string(),
        description: "Read one chapter daily".to_string(),
        frequency: "daily".to_string(),
    };

    let req = test::TestRequest::post()
        .uri("/habit")
        .set_json(&new_habit)
        .to_request();

    let resp: DefaultResponse = test::call_and_read_body_json(&mut app, req).await;

    assert_eq!(resp.status, "OK", "Expected default response for creating a habit");

}

#[actix_rt::test]
async fn test_check_habit() {
    let client = setup_redis().await;
    // First, insert a habit to check later
    let mut app = test::init_service(
        App::new()
            .app_data(client.clone())
            .route("/habit", web::post().to(create_habit)),
    )
    .await;

    let new_habit = NewHabit {
        name: "Exercise".to_string(),
        description: "Morning exercise session".to_string(),
        frequency: "daily".to_string(),
    };

    let create_req = test::TestRequest::post()
        .uri("/habit")
        .set_json(&new_habit)
        .to_request();
    let created_habit: Habit = test::call_and_read_body_json(&mut app, create_req).await;

    // Now test the check endpoint
    let check_uri = format!("/habit/{}/check", created_habit.id);
    let check_req = test::TestRequest::post().uri(&check_uri).to_request();
    let check_resp = test::call_service(&mut app, check_req).await;

    assert_eq!(
        check_resp.status(),
        actix_web::http::StatusCode::OK,
        "Expected OK status for checking habit"
    );
}

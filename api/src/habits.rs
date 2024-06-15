use log::{debug,warn,info,error};
use actix_web::Responder;
use actix_web::{web, HttpResponse};
use redis::{AsyncCommands, RedisError};
use crate::db_conn::{Habit, NewHabit, HabitCheckList,
                    HABITS_KEY, DefaultResponse, HABITS_CHECK_KEY};
use uuid::Uuid;

pub async fn get_habits(conn: web::Data<redis::Client>) -> impl Responder {
    info!("Getting habits");
    let mut habits: Vec<Habit> = Vec::new();

    let mut con = match conn.get_multiplexed_tokio_connection().await {
        Ok(con) => con,
        Err(_) => {
            error!("Failed to get connection to Redis");
            return HttpResponse::InternalServerError().json(habits)
        }
    };
    let habit_strs: Vec<String> = match con.hvals(&HABITS_KEY).await {
        Ok(habit_strs) => habit_strs,
        Err(_) => {
            warn!("{} key not found in Redis", HABITS_KEY);
            return HttpResponse::Ok().json(habits)
        }
    };

    // query all habit_strs at once
    for habit_str in habit_strs {
        let habit: Habit = match serde_json::from_str(&habit_str) {
            Ok(habit) => habit,
            Err(_) => {
                error!("Failed to parse habit: {}", habit_str);
                return HttpResponse::InternalServerError().json(habits)
            }
        };
        debug!("Retreived Habit: {:?}", habit.id);
        habits.push(habit);
    }

    HttpResponse::Ok().json(habits)
}

pub async fn create_habit(habit: web::Json<NewHabit>, conn: web::Data<redis::Client>) -> impl Responder {
    let mut con = conn.get_multiplexed_tokio_connection().await.expect("Connection failed");
    debug!("Creating habit: {:?}", habit.name);
    let id: String = Uuid::new_v4().to_string();
    let habit = Habit {
        id: id.clone(),
        name: habit.name.clone(),
        description: habit.description.clone(),
        create_dt: chrono::Utc::now(),
        frequency: habit.frequency.clone(),
    };
    let habit = serde_json::to_string(&habit).expect("Failed to serialize habit");
    debug!("Writing habit: {:?}", habit);
    let _: () = con.hset(&HABITS_KEY, id.clone(), habit).await.expect("Failed to write habit");
    // now create a corresponding check record
    let habit_check = HabitCheckList {
        id: id.clone(),
        check_dt: Vec::new(),
    };
    let habit_check = serde_json::to_string(&habit_check).expect("Failed to serialize habit check");
    debug!("Writing habit check: {:?}", habit_check);
    let _: () = con.hset(&HABITS_CHECK_KEY, id, habit_check).await.expect("Failed to write habit check");
    
    // return the default response and status code CREATED
    HttpResponse::Created().json(DefaultResponse::default())
}

pub async fn get_habit(habit_id: web::Path<String>, redis: web::Data<redis::Client>) -> impl Responder {
    let mut con = redis.get_multiplexed_tokio_connection().await.expect("Connection failed");
    let id: String = habit_id.into_inner();
    let habit: String = con.hget(&HABITS_KEY, &id).await.expect("Failed to read habit");
    let habit: Habit = serde_json::from_str(&habit).expect("Failed to parse habit");

    HttpResponse::Ok().json(habit)
}

pub async fn delete_habit(habit_id: web::Path<String>, redis: web::Data<redis::Client>) -> impl Responder {
    let mut con = redis.get_multiplexed_tokio_connection().await.expect("Connection failed");
    let id: String = habit_id.into_inner();
    let _: () = con.hdel(&HABITS_KEY, &id).await.expect("Failed to delete habit");

    HttpResponse::Ok().json(DefaultResponse::default())
}

pub async fn check_habit(habit_id: web::Path<String>, redis: web::Data<redis::Client>) -> impl Responder {
    let mut con = redis.get_multiplexed_tokio_connection().await.expect("Connection failed");
    let id: String = habit_id.into_inner();

    // get the habit check object corr. to the ID.
    let habit_check: Result<String, RedisError> = con.hget(&HABITS_CHECK_KEY, &id).await;
    let mut habit_check: HabitCheckList = match habit_check {
        Ok(habit_check) => serde_json::from_str(&habit_check).expect("Failed to parse habit check"),
        Err(_) => HabitCheckList {
            id: id.clone(),
            check_dt: Vec::new(),
        }
    };
    // append the current time to the check_dt list
    habit_check.check_dt.push(chrono::Utc::now());

    // write the updated habit check object back to Redis
    let habit_check = serde_json::to_string(&habit_check).expect("Failed to serialize habit check");
    let _: () = con.hset(&HABITS_CHECK_KEY, id.clone(), habit_check).await.expect("Failed to write habit check");

    let habit_check_list = _list_habit_checks(id, redis.get_ref()).await;
    HttpResponse::Ok().json(habit_check_list)
}

pub async fn list_habit_checks(habit_id: web::Path<String>, redis: web::Data<redis::Client>) -> impl Responder {
    let habit_check_list = _list_habit_checks(habit_id.into_inner(), redis.get_ref()).await;
    HttpResponse::Ok().json(habit_check_list)
}

pub async fn _list_habit_checks(id: String, redis: &redis::Client) -> HabitCheckList
{
    let mut con = redis.get_multiplexed_tokio_connection().await.expect("Connection failed");

    // get the habit check object corr. to the ID.
    // if it doesn't exist, initialise a new one
    let habit_check: Result<String, RedisError> = con.hget(&HABITS_CHECK_KEY, &id).await;
    log::debug!("Habit check: {:?}", habit_check);
    let habit_check: HabitCheckList = match habit_check {
        Ok(habit_check) => serde_json::from_str(&habit_check).expect("Failed to parse habit check"),
        Err(_) => HabitCheckList {
            id: id.clone(),
            check_dt: Vec::new(),
        }
    };
    habit_check
}

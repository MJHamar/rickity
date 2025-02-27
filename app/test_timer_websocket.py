#!/usr/bin/env python3
import asyncio
import json
import requests
import websockets
import uuid
import sys
import datetime

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# Utility functions
def create_timer(name, duration):
    """Create a new timer via the API"""
    response = requests.post(
        f"{API_URL}/timer",
        json={"name": name, "duration": duration}
    )
    if response.status_code != 200:
        print(f"Failed to create timer: {response.text}")
        sys.exit(1)
    return response.json()

async def websocket_client(client_id, timer_id, should_start=False):
    """Client that connects to a timer via WebSocket"""
    print(f"Client {client_id}: Connecting to timer {timer_id}")
    
    uri = f"{WS_URL}/timer/ws/{timer_id}"
    async with websockets.connect(uri) as websocket:
        # Log connection
        print(f"Client {client_id}: Connected")
        
        # If this client should start the timer, do it after a delay
        if should_start:
            await asyncio.sleep(2)  # Wait 2 seconds before starting
            print(f"Client {client_id}: Starting timer")
            await websocket.send(json.dumps({"action": "start"}))
        
        # Listen for updates
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] Client {client_id}: {data}")
                
                # If timer is stopped (reached 0), exit
                if data["timer_status"] == "stopped" and data["timer_state"] == 0:
                    print(f"Client {client_id}: Timer completed")
                    break
                
                # We'll only run for a limited time to demonstrate
                if data["timer_state"] <= 0:
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id}: Connection closed")

async def main():
    # Create a timer (3 seconds duration)
    timer_name = f"Test Timer {uuid.uuid4()}"
    timer = create_timer(timer_name, 3)
    timer_id = timer["id"]
    print(f"Created timer: {timer_name} (ID: {timer_id})")
    
    # Start two clients
    client1 = websocket_client("A", timer_id, should_start=True)   # This client will start the timer
    client2 = websocket_client("B", timer_id, should_start=False)  # This client will only observe
    
    # Run both clients concurrently
    await asyncio.gather(client1, client2)
    
    print("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 
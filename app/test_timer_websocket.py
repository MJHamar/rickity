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

# Utility function to check if timer is at zero
def is_timer_zero(hhmmss):
    """Check if a timer in HHmmss format is at zero"""
    return hhmmss == "000000"

async def websocket_client(client_id, timer_id, should_start=False, should_edit=False):
    """Client that connects to a timer via WebSocket"""
    print(f"Client {client_id}: Connecting to timer {timer_id}")
    
    uri = f"{WS_URL}/timer/ws/{timer_id}"
    async with websockets.connect(uri) as websocket:
        # Log connection
        print(f"Client {client_id}: Connected")
        
        # If this client should start the timer, do it after a delay
        start_timer_sent = False
        # If this client should edit the timer, do it immediately on first message
        edit_timer_sent = False
        
        # Listen for updates
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] Client {client_id}: {data}")
                
                # Edit the timer if we should and it's not running
                if should_edit and not edit_timer_sent and data["timer_status"] != "rolling":
                    new_time = "000010"  # 10 seconds in HHmmss format
                    print(f"Client {client_id}: Setting timer to {new_time}")
                    await websocket.send(json.dumps({"set": new_time}))
                    edit_timer_sent = True
                
                # Start the timer if needed (with delay)
                if should_start and not start_timer_sent:
                    await asyncio.sleep(2)  # Wait 2 seconds before starting
                    print(f"Client {client_id}: Starting timer")
                    await websocket.send(json.dumps({"action": "start"}))
                    start_timer_sent = True
                
                # If timer is stopped and at zero, exit
                if data["timer_status"] == "stopped" and is_timer_zero(data["timer_state"]):
                    print(f"Client {client_id}: Timer completed")
                    break
                
                # We'll only run for a limited time to demonstrate
                if is_timer_zero(data["timer_state"]):
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id}: Connection closed")

async def test_basic_timer():
    """Test basic timer functionality with multiple clients"""
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

async def test_editable_timer():
    """Test editable timer functionality"""
    # Create a timer (5 seconds duration)
    timer_name = f"Editable Timer {uuid.uuid4()}"
    timer = create_timer(timer_name, 5)
    timer_id = timer["id"]
    print(f"Created editable timer: {timer_name} (ID: {timer_id})")
    
    # First, connect a client that will edit the timer
    client_edit = websocket_client("Edit", timer_id, should_start=False, should_edit=True)
    
    # Run the edit client alone for a moment to ensure it has time to edit
    edit_task = asyncio.create_task(client_edit)
    
    # Wait to give time for the edit to happen
    await asyncio.sleep(3)
    
    # Then connect observer and starter clients
    client_observe = websocket_client("Observe", timer_id, should_start=False)
    client_start = websocket_client("Start", timer_id, should_start=True)
    
    # Run all clients concurrently
    await asyncio.gather(edit_task, client_observe, client_start)

async def main():
    # Test the basic timer functionality
    print("==== Testing Basic Timer ====")
    await test_basic_timer()
    
    # Wait a bit before the next test
    await asyncio.sleep(2)
    
    # Test the editable timer functionality
    print("\n==== Testing Editable Timer ====")
    await test_editable_timer()
    
    print("\nAll tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 
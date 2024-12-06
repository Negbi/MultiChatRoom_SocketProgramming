import csv
import json
import os.path
import socket
from typing import Any, Dict, Optional, Set

import auth
from chat_room import ChatRoom
from consts import FORMAT
from user_client import UserClient
from file_transfer import FileTransfer
from messages import send_success, send_failure

chat_rooms: Dict[str, ChatRoom] = {}

def load_chat_rooms_from_groups():
    if os.path.isfile("database/groups.csv"):
        with open("database/groups.csv", "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                name = row[0]
                chat_rooms[row[0]] = ChatRoom(name)

def get_message_json(conn: socket.socket) -> Any:
    request = conn.recv(1024).decode(FORMAT)
    if not request:
        print("Client terminated")
        return
    return json.loads(request)


def register(conn: socket.socket, request) -> None:
    """Registers the user with the given username and password."""
    print(f"Registering a new user. User name: {request['username']} Password: {request['password']}.\n")

    if auth.user_exists(request['username']):
        print(f"Failed to register user {request['username']}. User already exists.")
        send_failure(conn, "Username already exists")
    else:
        auth.register_user(request['username'], request['password'], request['role'])
        send_success(conn)


def validate_login(username: str, password: str) -> bool:
    """Validate a user's login credentials."""
    password_hash = auth.hash_password(password)
    with open("database/users.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username and row[1] == password_hash:
                return True
    return False

def change_password(conn: socket.socket, username: str, password: str) -> None:
    if not auth.user_exists(username):
        return send_failure(conn)
    auth.change_password(username, password)
    return send_success(conn)


def get_user_role(username: str) -> Optional[str]:
    """Retrieve the role for a given username from the users.csv file."""
    with open("database/users.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username:
                return row[2].strip()  # Assuming 'role' is in the third column.
    return None


def list_logged_users(conn: socket.socket):
    users_list = list_users(chat_rooms)
    send_success(conn, {
        "users": list(users_list)
    })

def upload_file(conn: socket.socket, room_name: str) -> None:
    request = conn.recv(1024).decode(FORMAT)
    if not request:
        print("Client terminated")
        return
    data = json.loads(request)
    size = data["size"]
    file_name = data["file_name"]
    transfer = FileTransfer(conn, file_name, room_name)
    transfer.download_file_from_client(size)
    send_success(conn, data={"status_code": 200, "message": "done uploading file"})

def download_file(conn: socket.socket, room_name: str) -> None:
    if not chat_rooms.get(room_name):
        send_failure(conn)
        return
    file_list = FileTransfer.get_file_names(room_name)
    send_success(conn, data={"file_list": file_list})
    message = get_message_json(conn)
    print(f"got message: {message}")
    file_name = message["file_name"]
    
    transfer = FileTransfer(conn, file_name, room_name)
    

    try:
        
        broadcast_lock = chat_rooms[room_name].broadcast_lock
        with broadcast_lock:
            transfer.upload_file_to_client()
        
        send_success(conn)
    except Exception as e:
        print(e)
        send_failure(conn)


def list_chat_rooms(conn):
    rooms = list_rooms()
    send_success(conn, {"rooms": rooms})


def create_room(conn: socket.socket, request: Any) -> None:
    """Create a new chat room and add it to the groups.csv file."""
    name = request["room_name"]
    print(f"Creating a new chat room: {name}")
    with open("database/groups.csv", "r+", newline="\n", encoding="utf-8") as file:
        existing_rooms = [line.strip() for line in file.readlines()]
        if name in existing_rooms:
            send_failure(conn, "Room already exists.")
        else:
            file.write(f"{name}\n")
            chat_rooms[name] = ChatRoom(name)
            send_success(conn)


def delete_room(conn: socket.socket, request: Any) -> None:
    """Delete a room and remove it from the groups.csv file."""
    name = request["chat_room_name"]
    print(f"Deleting chat room: {name}")
    with open("database/groups.csv", "r+", newline="\n", encoding="utf-8") as file:
        if name not in chat_rooms:
            send_failure(conn, "Chat room does not exist")
        else:
            rooms = [line for line in file if line.strip() != name]
            file.truncate(0)
            file.seek(0)
            file.writelines(rooms)
            chat_rooms.pop(name)
            try:
                os.remove("logs/chat_room_" + name + ".log")
            except OSError:
                print(f"Error: could not delete log for chat room {name}")
            send_success(conn)


def list_rooms():
    """List all chat rooms from the groups.csv file."""
    with open("database/groups.csv", "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)
        rooms = [row[0] for row in reader]
    return rooms


def list_users(chat_rooms):
    clients: Set[str] = set()
    for room in chat_rooms:
        for name, _ in chat_rooms[room].clients.items():
            clients.add(name)
    return clients


def enter_room(conn: socket.socket, username: str, room_name: str) -> UserClient:
    room = chat_rooms[room_name]
    if room is None:
        send_failure(conn, "Failed to join room.")
        return None
    else:
        user = UserClient(username, conn)
        room.add_client(user)
        send_success(conn, {
            "room": room_name,
            "messages": room.get_log()
        })
        return user

def login(conn: socket, request: Any):
    username = request["username"]
    password = request["password"]
    print(f"Logging in user: {username}")
    if validate_login(username, password):
        user_role = get_user_role(username)
        print(f"Logged in successfully, user role: {user_role}")
        send_success(conn, {
            "role": user_role
        })
        return user_role
    else:
        send_failure(conn, "Invalid username or password.")
        return None

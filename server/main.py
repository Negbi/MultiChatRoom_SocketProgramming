import json
import socket
import threading
import traceback
from typing import Optional, Tuple

from chat_room import ChatRoom
from consts import ADDR, FORMAT, HOST
from database_controller import DatabaseController
from functions import (change_password, chat_rooms, create_room, delete_room,
                       download_file, enter_room, list_chat_rooms,
                       list_logged_users, load_chat_rooms_from_groups, login,
                       register, upload_file)
from messages import send_failure
from user_client import UserClient


def internal_handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    print(f"[NEW CONNECTION] {addr} connected.")
    role: Optional[str] = None
    user_name: Optional[str] = None
    user: Optional[UserClient] = None
    logged_room: Optional[ChatRoom] = None
    connected: bool = True
    while connected:
        # Receiving the request type from the client (registration or login)
        raw_request = conn.recv(1024).decode(FORMAT)
        if not raw_request:
            print("Client terminated")
            break
        request = json.loads(raw_request)
        action = request["action"]
        if action == "register":
            register(conn, request)
        elif action == "login":
            role = login(conn, request)
            if role is not None:
                user_name = request.get("username")
                if user_name is None:
                    send_failure(conn, "You must specify a valid username")
        elif action == "exit":
            connected = False
            role = None
            conn.close()
            return
        elif action == "list_users":
            list_logged_users(conn)
        elif action == "create_chat_room":
            if role != "admin":
                send_failure(conn, "Only admins can create chat rooms")
                continue
            create_room(conn, request)
        elif action == "delete_chat_room":
            if role != "admin":
                send_failure(conn, "Only admins can delete chat rooms")
                continue
            delete_room(conn, request)
        elif action == "list_chat_rooms":
            list_chat_rooms(conn)
        elif action == "enter_room":
            room_name = request.get("room_name")
            if not room_name or room_name not in chat_rooms:
                send_failure(conn, "You must specify a valid room name")
                continue                
            user = enter_room(conn, user_name, room_name)
            if user is not None:
                logged_room = chat_rooms[room_name]
        elif action == "new_message":
            message = request["message"]
            if not message:
                send_failure(conn, "You must specify a valid message")
            if message == "/exit":
                if logged_room is None:
                    send_failure(conn, "You must be in a chat room to exit")
                if not user:
                    send_failure(conn, "You must be logged in to exit")
                logged_room.remove_client(user)
            elif message == "/upload":
                if not room_name:
                    send_failure(conn, "You must be in a chat room to upload")
                upload_file(conn, room_name)
            elif message == "/download":
                if not room_name:
                    send_failure(conn, "You must be in a chat room to download")
                download_file(conn, room_name)
            else:
                if not user:
                    send_failure(conn, "You must be logged in to send messages")
                if not room_name:
                    send_failure(conn, "You must be in a chat room to send messages")
                logged_room.broadcast(message, user)
        elif action == "change_password":
            password = request["password"]
            change_password(conn, user_name, password)
        else:
            send_failure(conn, "Invalid action")

    conn.close()
    print(f"[CONNECTION CLOSED] {addr} disconnected.")


def handle_client(conn, addr):
    """
    This function handles client connections to the server.

    :param conn: The connection object for the client
    :param addr: The address of the client
    :return: None
    """
    try:
        internal_handle_client(conn, addr)
    except Exception as e:
        print(f"[ERROR] occurred while handling client connection: {e}")
        # print traceback
        traceback.print_exc()
        conn.close()


def start_server():
    """
    This function starts the server and listens for connections
    to the server.

    :return: None
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(ADDR)
    server_socket.listen()
    print(f"[LISTENING] Server is listening on {HOST}")
    load_chat_rooms_from_groups()
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


def main():
    DatabaseController()
    print("[STARTING] Server is starting...")
    start_server()


if __name__ == "__main__":
    main()

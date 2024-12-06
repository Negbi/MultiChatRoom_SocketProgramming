import select
import socket
import threading
import traceback
from typing import Optional
from file_transfer import FileTransfer
from consts import FORMAT
from messages import receive_message_json, send_message_json


def register(client: socket.socket, role: str) -> None:
    """
    Register the user with the server.

    Args:
        client (socket.socket): The client socket.
        role (str): The user's role.
    """
    print("Registering a new user...")
    print("Please enter a username and password to register.")
    username = input("Username: ")
    password = input("Password: ")
    data = {
        "action": "register",
        "role": role,
        "username": username,
        "password": password,
    }
    send_message_json(client, data)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        print(f"User {username} registered successfully.")
    else:
        print(f"Registration failed - {response['error_message']}.")


def read_messages(
    connection: socket.socket,
    close_read_thread: threading.Event,
    read_lock: threading.Lock,
) -> None:
    """
    Read incoming messages from the client and send them to the server.

    Args:
        connection (socket.socket): The client socket.
        close_read_thread (threading.Event): A flag that indicates whether
                                             or not the thread should stop.
        read_lock (threading.Lock): A lock that is used to synchronize the
                                    thread with other threads(for download).
    """
    while True:
        try:
            read_conn, _, _ = select.select([connection], [], [], 0.1)
            if close_read_thread.is_set():
                print("stopped reading incoming messages from channel")
                break
            with read_lock:
                if read_conn:
                    message = connection.recv(1024).decode(FORMAT)
                    print("\r< ", message + "\n> ", end="")
        except Exception as e:
            if isinstance(e, ConnectionError):
                print("Connection closed by server.")
                break
            traceback.print_exc()


def login(client: socket.socket) -> None:
    """
    Login function for the server

    Args:
        client (socket.socket): The client socket
    """
    print("Enter username and password to login:")
    username = input("Enter username: ")
    password = input("Enter password: ")
    data = {"action": "login", "username": username, "password": password}
    send_message_json(client, data)
    response = receive_message_json(client)
    role = None
    if response["status_code"] == 200:
        role = response["role"]
        print(f"Logged-in as {role} successfully.")
        run_login_menu(client, role)
    else:
        print(f"Login failed - {response['error_message']}.")
        return


def run_login_menu(client: socket.socket, role: str) -> None:
    """
    Run the login menu for a given role

    Args:
        client (socket.socket): The client socket
        role (str): The user's role
    """
    while True:
        print("\n")
        if role == "admin":
            print_admin_chat_menu()
        elif role == "user":
            print_user_chat_menu()

        menu_selection = input("Select an option: ")

        if menu_selection == "1":
            do_chat(client)
        elif menu_selection == "2":
            do_change_password(client)
        elif menu_selection == "3":
            do_list_users(client)
        elif menu_selection == "4":
            do_create_chat_room(client)
        elif menu_selection == "5":
            do_delete_chat_room(client)
        elif menu_selection == "/exit":
            client.close()
            exit()
        else:
            print("Invalid option. Please enter a valid option.")


def do_chat(client: socket.socket) -> None:
    """
    Enter the chat menu and start a new chat session

    Args:
        client (socket.socket): The client socket
    """
    rooms = list_chat_rooms(client)
    if rooms is None:
        print("Error getting group list")
        return
    elif len(rooms) == 0:
        print("There are no available rooms")
        return
    else:
        print("Chat rooms: ")
        for room in rooms:
            print(room)

    room_name = input("Enter chat room name: ")
    do_enter_room(client, room_name)


def do_change_password(client: socket.socket) -> None:
    """
    Change A given user's password

    Args:
        client (socket.socket): The client socket
    """
    password = input("Enter new password: ")
    data = {"action": "change_password", "password": password}
    send_message_json(client, data)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        print("Password changed successfully")
    else:
        print(f"Error Changing password: {response['error_message']}")


def do_list_users(client: socket.socket) -> None:
    """
    List all users in the system

    Args:
        client (socket.socket): The client socket
    """
    data = {"action": "list_users"}
    send_message_json(client, data)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        print("Logged-in users conencted to a room:")
        for user in response["users"]:
            print(user)
    else:
        print(f"Error getting user list: {response['error_message']}")


def do_create_chat_room(client: socket.socket) -> None:
    """
    Create a new chat room for users to join

    Args:
        client (socket.socket): The client socket
    """
    chat_room_name = input("Enter new chat room name: ")
    data = {"action": "create_chat_room", "room_name": chat_room_name}
    send_message_json(client, data)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        print(f"Room {chat_room_name} created successfully")
    else:
        print(f"Error creating chat room - {response['error_message']}")


def do_delete_chat_room(client: socket.socket) -> None:
    """
    Delete a chat room by name

    Args:
        client (socket.socket): The client socket
    """
    rooms = list_chat_rooms(client)

    rooms_list = "\n".join(f"- {room}" for room in rooms)
    chat_room_name = input(f"Enter chat room name to delete: \n{rooms_list}\n")

    data = {"action": "delete_chat_room", "chat_room_name": chat_room_name}
    send_message_json(client, data)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        print(f"Room {chat_room_name} has been deleted")
    else:
        print(f"Error deleting chat room - {response['error_message']}")


def list_chat_rooms(client: socket.socket) -> Optional[str]:
    """
    List all chat rooms

    Args:
        client (socket.socket): The client socket

    Returns:
        Optional[str]: The list of chat rooms or None on error
    """
    data = {"action": "list_chat_rooms"}
    send_message_json(client, data)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        return response["rooms"]
    else:
        return None


def upload_file(conn: socket.socket) -> None:
    """
    Upload a file

    Args:
        conn (socket.socket): The client socket
    """
    path_to_upload = input("Enter the path to upload: ")
    transfer = FileTransfer(conn, path_to_upload)
    transfer.upload_file()
    response = receive_message_json(conn)
    if response["status_code"] == 200:
        print("File uploaded successfully")
    else:
        print("Error uploading file")


def download_file(conn: socket.socket) -> None:
    """
    Download a file

    Args:
        conn (socket.socket): The client socket
    """
    message = receive_message_json(conn)
    files = "\n".join(message["file_list"])
    file_name = input(f"Choose file from list: \n{files}\n")
    print(f"file name: {file_name}")
    send_message_json(conn, {"file_name": str(file_name)})
    response = receive_message_json(conn)
    print(f"response: {response}")
    file_size = response["size"]
    transfer = FileTransfer(conn, file_name)
    transfer.download_file_from_server(file_size)
    response = receive_message_json(conn)
    if response["status_code"] == 200:

        print("File downloaded successfully")
    else:
        print("Error downloading file")


def do_enter_room(client: socket.socket, room_name: str) -> None:
    """
    Enter a room and allow the user to chat with other users in that room

    Args:
        client (socket.socket): The client socket
        room_name (str): The of the room to enter
    """
    enter_room_request = {"action": "enter_room", "room_name": room_name}
    send_message_json(client, enter_room_request)
    response = receive_message_json(client)
    if response["status_code"] == 200:
        print(f"Joined room: {room_name}")
        print(f"Replaying chat messages from room {room_name}")
        for message in response["messages"]:
            print(message)
        print("\nReplayed all messages")
        print("use /help to see available commands")


        close_read_thread = threading.Event()
        read_lock = threading.Lock()
        read_thread = threading.Thread(
            target=read_messages, args=(client, close_read_thread, read_lock)
        )
        read_thread.start()
        while True:
            message = input("> ")
            if message:
                send_message_json(client, {"action": "new_message", "message": message})
                if message == "/help":
                    print("Available commands:\n/help\n/exit\n/upload\n/download")
                elif message == "/exit":
                    close_read_thread.set()
                    read_thread.join()
                    break
                elif message == "/upload":
                    with read_lock:
                        upload_file(client)
                elif message == "/download":
                    with read_lock:
                        download_file(client)
    else:
        print(f"Error entering chat room - {response['error_message']}")


def print_user_chat_menu() -> None:
    """
    Prints the user menu for a chat client
    """
    print("1. Enter chat room")
    print("2. Change password")
    print("3. List logged in users")
    print("/exit to exit")


def print_admin_chat_menu() -> None:
    """
    Prints the admin menu for a chat client
    """
    print("1. Enter chat room")
    print("2. Change password")
    print("3. List logged in users")
    print("4. Create a new chat room")
    print("5. Delete a chat room")
    print("/exit to exit")

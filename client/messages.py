import json
import socket
from typing import Any

from consts import FORMAT


def send_message(client: socket.socket, message: str) -> None:
    """
    Utility function to send encoded messages to the server.
    """
    client.send(message.encode(FORMAT))


def send_message_json(client: socket.socket, message: str) -> None:
    """
    Utility function to send encoded messages to the server.
    """
    client.send(json.dumps(message).encode(FORMAT))


def receive_message(client_socket: socket.socket) -> str:
    """
    Utility function to receive and decode messages from the server.
    """
    return client_socket.recv(1024).decode(FORMAT)


def receive_message_json(client_socket: socket.socket) -> Any:
    """
    Utility function to receive and decode messages from the server.
    """
    full_message = ""
    while True:
        message = client_socket.recv(1024).decode(FORMAT)
        full_message += message
        if message is None or len(message) < 1024:
            break

    return json.loads(full_message)

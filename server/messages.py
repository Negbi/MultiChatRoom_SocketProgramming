
import json
import socket
from consts import FORMAT

def send_success(conn: socket.socket, data=None) -> None:
    message = {}
    if data is None:
        message = {
            "status_code": 200
        }
    else:
        message["status_code"] = 200
        for key, value in data.items():
            message[key] = value
    conn.send(json.dumps(message).encode(FORMAT))


def send_failure(conn: socket.socket, error_message="") -> None:
    message = {
        "status_code": 400,
        "error_message": error_message,
    }
    conn.send(json.dumps(message).encode(FORMAT))
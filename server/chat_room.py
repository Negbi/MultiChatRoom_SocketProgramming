import os.path
import threading
import time
from typing import Dict
from messages import send_failure

from user_client import UserClient


class ChatRoom:
    message_rate_limit: int = 10
    def __init__(self, name: str):
        self.name = name
        self.clients: Dict[str, UserClient] = {}
        self.broadcast_lock = threading.Lock()

    def add_client(self, client: UserClient) -> None:
        if client.name not in self.clients:
            self.clients[client.name] = client

    def remove_client(self, client: UserClient) -> None:
        if client.name in self.clients:
            del self.clients[client.name]

    def log_message(self, message: str) -> None:
        with open("logs/chat_room_" + self.name + ".log", "a+", encoding="utf-8") as f:
            f.write(message + "\n")

    def get_log(self) -> None:
        file_name = "logs/chat_room_" + self.name + ".log"
        if not os.path.isfile(file_name):
            return []
        else:
            with open(file_name, "r", encoding="utf-8") as f:
                messages = f.readlines()
                messages = [line.strip() for line in messages]
            return messages

    def replay_log(self, client: UserClient) -> None:
        file_name = "logs/chat_room_" + self.name + ".log"
        if not os.path.isfile(file_name):
            client.conn.send(
                "replaying all messages from the group chat\n".encode("utf-8")
            )
            client.conn.send("done replaying messages.".encode("utf-8"))
        else:
            client.conn.send(
                            "replaying all messages from the group chat\n".encode("utf-8")
                        )
            with open(file_name, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    try:
                        client.conn.send((line.strip() + "\n").encode("utf-8"))
                    except Exception as e:
                        print(
                            f"Failed to send message to {client.name} ({e}), removing client from list"
                        )
            client.conn.send("done replaying messages.".encode("utf-8"))

    def check_if_user_passed_message_rate_limit(self, user: UserClient) -> bool:
        if len(user.rolling_last_message_time) == user.rolling_last_message_time.maxlen:
            if user.rolling_last_message_time[-1] > time.time() - 30:
                return True
        return False

    def update_last_message_time(self, user):
        user.rolling_last_message_time.append(time.time())

    def broadcast(self, message: str, sender: UserClient) -> None:
        if self.check_if_user_passed_message_rate_limit(sender):
            send_failure(sender.conn, f"You can only send {sender.rolling_last_message_time.maxlen} messages every 30 seconds")
            return
        self.update_last_message_time(sender)
        
        self.log_message(sender.name + ":" + message)
        clients_to_remove = []
        for name, client in self.clients.items():
            if name != sender.name:
                try:
                    with self.broadcast_lock:
                        client.conn.send((sender.name + ": " + message).encode("utf-8"))
                except Exception as e:
                    print(
                        f"Failed to send message to user: {client.name} ({e}), removing client from list"
                    )
                    clients_to_remove.append(name)

        # remove dead clients from list
        for name in clients_to_remove:
            disconnected_client = self.clients.pop(name)
            try:
                disconnected_client.conn.close()
                print("Client disconnected successfully on deletion")
            except Exception as e:
                print(f"Failed to close connection with {disconnected_client.name} ({e})")

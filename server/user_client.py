from collections import deque
import time


class UserClient:
    def __init__(self, name, conn):
        self.name = name
        self.conn = conn
        self.rolling_last_message_time: deque[time.time] = deque(maxlen=5)
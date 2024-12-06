import csv
import os


class DatabaseController:
    def __init__(self) -> None:
        if not os.path.exists("database"):
            os.mkdir("database")
        self.initialize_user_database()
        self.initialize_group_database()
        self.initialize_logs()
        self.initialize_files()
        print("DatabaseController initialized")

    def initialize_user_database(self):
        if not os.path.exists("database/users.csv"):
            with open("database/users.csv", "w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password_hash", "role"])

    def initialize_group_database(self):
        if not os.path.exists("database/groups.csv"):
            with open("database/groups.csv", "w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["group_name"])

    def initialize_logs(self):
        if not os.path.exists("logs"):
            os.mkdir("logs")

    def initialize_files(self):
        if not os.path.exists("files"):
            os.mkdir("files")
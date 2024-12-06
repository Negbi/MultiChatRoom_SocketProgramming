import csv
import hashlib

# User management functions (previously outlined)


def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password, role):
    """Register a new user with a hashed password and role."""
    password_hash = hash_password(password)
    with open("database/users.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([username, password_hash, role])


def user_exists(username):
    """Check if a user already exists."""
    with open("database/users.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username:
                return True
    return False

def change_password(username, password):
    """Change a user's password."""
    password_hash = hash_password(password)
    with open("database/users.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        data = list(reader)
        for row in data:
            if row[0] == username:
                row[1] = password_hash
                break
    with open("database/users.csv", "w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)


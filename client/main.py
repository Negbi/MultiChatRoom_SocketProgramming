import socket
from consts import ADDR

from functions import login, register
from messages import send_message

CLIENT_OPTIONS = "Please choose an action:\n1. Register\n2. Login\n3. Exit\n4. Register As Admin"

def start_client():
    """
    Starts the client and handles all the user interactions
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        while True:
            print(CLIENT_OPTIONS)
            choice = input("Enter your choice (1-4): ")
            if choice == "1":
                register(client_socket, "user")
            elif choice == "2":
                login(client_socket)
            elif choice == "3":
                send_message(client_socket, "exit")
                break
            elif choice == "4":
                register(client_socket, "admin")
            else:
                print("Invalid option. Please enter a valid option.\n")
        try:
            client_socket.close()
        except OSError:
            pass
    except Exception as e:
        print(f"Error connecting to server {e}. Exiting...")
        return


def main() -> None:
    """
    Main function for the client.
    """
    print("[CLIENT] Starting client...")
    start_client()


if __name__ == "__main__":
    main()

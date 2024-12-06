import os.path
import socket
import messages


class FileTransfer:
    """
    Class the file transfer between client and server

    Args:
        server (socket.socket): the socket of the client
        file_name (str): the name of the file to be

    Raises:
        FileNotFoundError: if the file does not exist
    """

    download_folder = "files"

    def __init__(self, server: socket.socket, file_name: str):
        self.server = server
        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder)
        self.file_path = os.path.join(self.download_folder, file_name)

    def upload_file(self) -> None:
        """
        upload the file to server

        Raises:
            FileNotFoundError: if the file does not exist
        """
        if not os.path.exists(self.file_path):
            print("File to upload not found: " + self.file_path)
            raise FileNotFoundError(self.file_path)

        # read file size
        messages.send_message_json(
            self.server,
            {
                "size": os.path.getsize(self.file_path),
                "file_name": os.path.basename(self.file_path).split("/")[-1],
            },
        )

        # read file
        with open(self.file_path, "rb") as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                self.server.send(data)

        print("File sent over")

    def download_file_from_server(self, file_size: int) -> None:
        """
        Download a file from server to client

        Args:
            file_size (_type_): the size of the file to be downloaded
        """
        bytes_received = 0
        with open(self.file_path, "wb") as file:
            # read all bytes until the first \0
            while True:
                if bytes_received >= file_size:
                    break
                bytes_to_read = file_size - bytes_received
                data = self.server.recv(bytes_to_read)
                bytes_received += len(data)
                file.write(data)

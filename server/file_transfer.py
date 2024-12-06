import os.path
import socket
from messages import send_success

class FileTransfer:
    download_folder = 'files'
    
    @staticmethod
    def get_file_names(group_name: str):
        return os.listdir(os.path.join(FileTransfer.download_folder, group_name))
    def __init__(self, client: socket.socket, name: str, group_name: str):
        self.sender = client
        self.name = name
        self.download_folder = os.path.join(self.download_folder, group_name)
        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder)
        self.file_path = os.path.join(self.download_folder, self.name)
        
            
    def download_file_from_client(self, file_size):
        bytes_received = 0
        with open(self.file_path, 'wb') as file:
            while True:
                if bytes_received >= file_size:
                    break
                data = self.sender.recv(1024)
                bytes_received += len(data)
                file.write(data)

    def upload_file_to_client(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(self.file_path)
                # read file size
                
        send_success(self.sender, data={"size": os.path.getsize(self.file_path), "file_name": os.path.basename(self.file_path).split('/')[-1] })

        # read file
        with open(self.file_path, "rb") as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                self.sender.send(data)

        
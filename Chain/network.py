import socket
import threading
import json
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from node import Node
    
    
class Server:
    def __init__(self, host: str, port: int, node: 'Node'):
        self.host: str = host
        self.port = port
        self.node: 'Node' = node
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients: List = []
        self.running: bool = True

    def start(self) -> None:
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self) -> None:
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except:
                break

    def handle_client(self, client_socket) -> None:
        while self.running:
            try:
                message_bytes = client_socket.recv(1024)
                if message_bytes:
                    message: json = json.loads(message_bytes.decode('utf-8'))
                    self.node.receive_message(message)
                else:
                    self.node.receive_message(message)
            except:
                break
        client_socket.close()

    def broadcast(self, message: str) -> None:
        message_bytes: json = json.dumps(message).encode('utf-8')
        for client in self.clients:
            try:
                client.sendall(message_bytes)
            except:
                self.clients.remove(client)

    def stop(self) -> None:
        self.running: bool = False
        for client in self.clients:
            client.close()
        self.server_socket.close()


class Client:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def send_message(self, message: str) -> None:
        message_bytes: json = json.dumps(message).encode('utf-8')
        self.client_socket.sendall(message_bytes)

    def close(self) -> None:
        self.client_socket.close()

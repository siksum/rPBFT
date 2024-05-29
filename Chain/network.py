import socket
import threading
import json


class Server:
    def __init__(self, host, port, node):
        self.host = host
        self.port = port
        self.node = node
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients = []
        self.running = True

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
                    message = json.loads(message_bytes.decode('utf-8'))
                    self.node.receive_message(message)
                else:
                    break
            except:
                break
        client_socket.close()

    def broadcast(self, message: str) -> None:
        message_bytes = json.dumps(message).encode('utf-8')
        for client in self.clients:
            try:
                client.sendall(message_bytes)
            except:
                self.clients.remove(client)

    def stop(self) -> None:
        self.running = False
        for client in self.clients:
            client.close()
        self.server_socket.close()


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def send_message(self, message: str) -> None:
        meessage_bytes= json.dumps(message).encode('utf-8')
        self.client_socket.sendall(meessage_bytes)

    def close(self) -> None:
        self.client_socket.close()

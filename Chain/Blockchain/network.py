import socket
import threading
import json
import logging
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Consensus.node import Node


class Server:
    def __init__(self, host: str, port: int, node: 'Node'):
        self.host: str = host
        self.port: int = port
        self.node: 'Node' = node
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients: List[socket.socket] = []
        self.running: bool = True
        self.clients_lock = threading.Lock()
    

    def start(self) -> None:
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self) -> None:
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                with self.clients_lock:
                    self.clients.append(client_socket)
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except (socket.error, OSError) as e:
                logging.error(f"Socket error while receiving data: {e}")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                logging.error("Traceback information:", exc_info=True)
                break

    def handle_client(self, client_socket: socket.socket) -> None:
        # client_socket.settimeout(10)
        
        buffer = ""
        try:
            while self.running:
                # try:
                message_bytes = client_socket.recv(1024)
                if not message_bytes:
                    break  # 클라이언트가 연결을 종료한 경우

                buffer += message_bytes.decode('utf-8')
                logging.debug(f"Buffer content: {buffer}")

                # 줄바꿈 문자를 기준으로 메시지 분리
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message.strip():
                        try:
                            parsed_message = json.loads(message)
                            logging.debug(f"Parsed message: {parsed_message}")
                            self.node.receive_message(parsed_message)
                        except json.JSONDecodeError:
                            logging.error(f"JSON decoding error with message: {message}")
                            buffer = ""

                # except OSError as e:
                #     logging.error(f"Socket error while receiving data: {e}")
                #     logging.error("Traceback information:", exc_info=True)
                #     break

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            logging.error(f"Buffer content at error: {buffer}")
            logging.error("Traceback information:", exc_info=True)
        finally:
            client_socket.close()

    def broadcast(self, message: dict) -> None:
        message_bytes = (json.dumps(message) + '\n').encode('utf-8')
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.sendall(message_bytes)
                except (BrokenPipeError, IOError):
                    self.clients.remove(client)

    def stop(self) -> None:
        self.running = False
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.close()
                except (BrokenPipeError, IOError) as e:
                    logging.error(f"Socket error during shutdown: {e}")
        self.server_socket.close()


class Client:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self) -> None:
        try:
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            logging.error(f"Connection failed: {e}")

    def send_message(self, message: dict) -> None:
        if self.client_socket.fileno() == -1:
            logging.error("Socket is invalid. Attempting to reconnect.")
            self.connect()

        try:
            message_bytes = (json.dumps(message) + '\n').encode('utf-8')
            self.client_socket.sendall(message_bytes)
        except (BrokenPipeError, IOError) as e:
            logging.error(f"Socket error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def close(self) -> None:
        try:
            self.client_socket.close()
        except Exception as e:
            logging.error(f"Error closing socket: {e}")

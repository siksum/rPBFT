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
        self.port = port
        self.node: 'Node' = node
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.clients: List = []
        self.running: bool = True
        self.clients_lock = threading.Lock()

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
        buffer = ""
        try:
            while self.running:
                message_bytes = client_socket.recv(1024)
                if message_bytes:
                    buffer += message_bytes.decode('utf-8')
                    
                    while buffer:
                        try:
                            message, index = json.JSONDecoder().raw_decode(buffer)
                            buffer = buffer[index:].lstrip()  # 이미 처리된 부분 제거
                            self.node.receive_message(message)
                        except json.JSONDecodeError:
                            break  # 현재 버퍼가 완전한 JSON 메시지를 포함하지 않음

                else:
                    break  # 클라이언트가 연결을 종료한 경우

        except (BrokenPipeError, ConnectionResetError) as e:
            logging.error(f"Socket error: {e}")
        except json.JSONDecodeError as e:
            # logging.error(f"JSON decoding error: {e}")
            # logging.error(f"Partial buffer content: {buffer}")
            # logging.error(f"Error Location: {e.lineno}:{e.colno} (char {e.pos})")
            logging.error(f"JSON decoding error")
            logging.error(f"Partial buffer content")
            logging.error(f"Error Location")
        except Exception as e:
            # logging.error(f"Unexpected error: {e}")
            # logging.error(f"Buffer content at error: {buffer}")
            # logging.error("Traceback information:", exc_info=True)
            logging.error(f"Unexpected error")
            logging.error(f"Buffer content at error")
            logging.error("Traceback information:")
        finally:
            try:
                if client_socket.fileno() != -1:
                    client_socket.close()
            except Exception as e:
                # logging.error(f"Error closing client socket: {e}")
                logging.error(f"Error closing client socket")


    def broadcast(self, message: str) -> None:
        message_bytes: json = json.dumps(message).encode('utf-8')
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.sendall(message_bytes)
                except:
                    self.clients.remove(client)

    def stop(self) -> None:
        self.running: bool = False
        # for client in self.clients:
        #     try:
        #         client.close()
        #         print("Server stopped.")
                
        #     except (BrokenPipeError, IOError) as e:
        #         print(f"소켓 오류 발생: {e}")
        self.server_socket.close()


class Client:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def send_message(self, message: str) -> None:
        if self.client_socket.fileno() == -1:
            logging.error("Socket is invalid. Attempting to reconnect.")
            self.client_socket.connect((self.host, self.port))
        try:
            message_bytes = json.dumps(message).encode('utf-8')
            self.client_socket.sendall(message_bytes)
        except (BrokenPipeError, IOError) as e:
            logging.error(f"Socket error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def close(self) -> None:
        self.client_socket.close()
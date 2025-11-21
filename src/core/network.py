import socket
import threading
import json
import os
import logging
from typing import Callable, Optional
from .protocol import Message, MessageType, TCP_PORT, BUFFER_SIZE

class NetworkManager:
    def __init__(self, username: str, on_message: Callable[[Message], None], on_file_progress: Callable[[str, int, int], None] = None):
        self.username = username
        self.on_message = on_message
        self.on_file_progress = on_file_progress
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.logger = logging.getLogger("NetworkManager")
        self.active_transfers = {} # file_id -> file_handle

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('', TCP_PORT))
            self.server_socket.listen(5)
            threading.Thread(target=self._accept_loop, daemon=True).start()
            self.logger.info(f"TCP Server started on port {TCP_PORT}")
        except OSError as e:
            self.logger.error(f"Failed to bind TCP port {TCP_PORT}: {e}")
            self.running = False

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("TCP Server stopped.")

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
            except OSError:
                break
            except Exception as e:
                self.logger.error(f"Error accepting connection: {e}")

    def _handle_client(self, sock: socket.socket, addr):
        ip = addr[0]
        try:
            while self.running:
                # Read length prefix (4 bytes)
                length_bytes = sock.recv(4)
                if not length_bytes:
                    break
                
                msg_len = int.from_bytes(length_bytes, byteorder='big')
                
                # Read message body
                data = b''
                while len(data) < msg_len:
                    chunk = sock.recv(min(msg_len - len(data), BUFFER_SIZE))
                    if not chunk:
                        break
                    data += chunk
                
                if len(data) != msg_len:
                    break

                msg = Message.from_bytes(data)
                msg.sender_ip = ip # Ensure IP is correct from socket
                
                if msg.type == MessageType.FILE_DATA:
                    self._handle_file_data(msg)
                else:
                    self.on_message(msg)

        except Exception as e:
            self.logger.error(f"Connection error with {ip}: {e}")
        finally:
            sock.close()

    def _handle_file_data(self, msg: Message):
        # Basic file handling - in a real app this would be more robust
        # For now, we assume FILE_OFFER was accepted and we just write data
        file_name = msg.payload.get('filename')
        data_chunk = msg.payload.get('data').encode('latin1') # Re-encode binary data if it was JSON stringified
        
        # This is a simplified placeholder. 
        # In a robust implementation, we'd handle file streams separately or use a raw socket mode for files.
        # Given the JSON protocol, sending large files as JSON strings is inefficient.
        # A better approach for this specific requirement (simple, robust) might be to open a separate connection for file transfer
        # or switch to raw bytes after a header.
        # However, sticking to the plan and protocol for simplicity of the first iteration.
        pass

    def send_message(self, target_ip: str, message: str):
        msg = Message(
            type=MessageType.TEXT,
            sender_name=self.username,
            sender_ip="", 
            payload={'text': message}
        )
        self._send_to_peer(target_ip, msg)

    def send_file_offer(self, target_ip: str, filepath: str):
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        msg = Message(
            type=MessageType.FILE_OFFER,
            sender_name=self.username,
            sender_ip="",
            payload={'filename': filename, 'filesize': filesize}
        )
        self._send_to_peer(target_ip, msg)

    def _send_to_peer(self, ip: str, msg: Message):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, TCP_PORT))
            
            data = msg.to_bytes()
            length_bytes = len(data).to_bytes(4, byteorder='big')
            
            sock.sendall(length_bytes + data)
            sock.close()
        except Exception as e:
            self.logger.error(f"Failed to send to {ip}: {e}")
            raise e

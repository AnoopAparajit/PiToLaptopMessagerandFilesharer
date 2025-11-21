import socket
import threading
import time
import logging
from typing import Dict, Callable, Optional
from .protocol import Message, MessageType, UDP_PORT, BROADCAST_IP, DISCOVERY_INTERVAL

class PeerDiscovery:
    def __init__(self, username: str, on_peer_discovered: Callable[[str, str], None], on_peer_lost: Callable[[str], None]):
        self.username = username
        self.on_peer_discovered = on_peer_discovered
        self.on_peer_lost = on_peer_lost
        self.running = False
        self.peers: Dict[str, float] = {}  # ip -> last_seen_timestamp
        self.peer_names: Dict[str, str] = {} # ip -> username
        self.broadcast_socket: Optional[socket.socket] = None
        self.listen_socket: Optional[socket.socket] = None
        self.logger = logging.getLogger("PeerDiscovery")

    def start(self):
        self.running = True
        
        # Setup Broadcast Socket
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Setup Listen Socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.listen_socket.bind(('', UDP_PORT))
        except OSError as e:
            self.logger.error(f"Failed to bind UDP port {UDP_PORT}: {e}")
            self.running = False
            return

        # Start Threads
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        self.logger.info("Peer Discovery started.")

    def stop(self):
        self.running = False
        if self.broadcast_socket:
            self.broadcast_socket.close()
        if self.listen_socket:
            self.listen_socket.close()
        self.logger.info("Peer Discovery stopped.")

    def _broadcast_loop(self):
        while self.running:
            try:
                msg = Message(
                    type=MessageType.DISCOVERY,
                    sender_name=self.username,
                    sender_ip="", # Receiver will determine IP
                    payload={}
                )
                data = msg.to_bytes()
                self.broadcast_socket.sendto(data, (BROADCAST_IP, UDP_PORT))
            except Exception as e:
                self.logger.error(f"Error broadcasting: {e}")
            time.sleep(DISCOVERY_INTERVAL)

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.listen_socket.recvfrom(4096)
                sender_ip = addr[0]
                
                # Ignore own broadcasts (simple check, can be improved)
                # Ideally we check against local interfaces, but for now we rely on logic
                
                try:
                    msg = Message.from_bytes(data)
                    if msg.type == MessageType.DISCOVERY:
                        self._handle_discovery(sender_ip, msg.sender_name)
                except Exception as e:
                    self.logger.error(f"Error parsing discovery message: {e}")

            except OSError:
                # Socket closed
                break
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")

    def _handle_discovery(self, ip: str, name: str):
        # If we receive our own broadcast, we might want to filter it out.
        # For simplicity, we'll assume the UI/Network manager handles "self" check 
        # or we filter by checking if IP is one of ours. 
        # For now, let's just register it.
        
        current_time = time.time()
        is_new = ip not in self.peers
        
        self.peers[ip] = current_time
        self.peer_names[ip] = name
        
        if is_new:
            self.on_peer_discovered(ip, name)

    def _cleanup_loop(self):
        while self.running:
            time.sleep(5)
            current_time = time.time()
            to_remove = []
            for ip, last_seen in self.peers.items():
                if current_time - last_seen > (DISCOVERY_INTERVAL * 3):
                    to_remove.append(ip)
            
            for ip in to_remove:
                del self.peers[ip]
                if ip in self.peer_names:
                    del self.peer_names[ip]
                self.on_peer_lost(ip)

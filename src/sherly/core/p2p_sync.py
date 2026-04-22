import json
import base64
import socket
import threading
import time
from sherly.core.encryption import StorageEncryption
from sherly.utils.runtime_utils import log

class P2PSync:
    """
    Handles encrypted P2P state synchronization between Sherly instances.
    Uses UDP broadcasting for local discovery.
    """
    def __init__(self, node_id: str, port: int = 5556):
        self.node_id = node_id
        self.port = port
        self.encryption = StorageEncryption()
        self.running = False
        self.peers = set()

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._broadcast_presence, daemon=True, name="P2PBroadcast").start()
        threading.Thread(target=self._listen_for_peers, daemon=True, name="P2PListen").start()
        log(f"[P2P] Sync node {self.node_id} started on port {self.port}")

    def _broadcast_presence(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while self.running:
                msg = json.dumps({"node_id": self.node_id, "port": self.port, "type": "discovery"})
                s.sendto(msg.encode(), ('<broadcast>', self.port))
                time.sleep(10)

    def _listen_for_peers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', self.port))
            s.settimeout(1.0)
            while self.running:
                try:
                    data, addr = s.recvfrom(1024)
                    msg = json.loads(data.decode())
                    if msg.get("node_id") != self.node_id:
                        peer = (addr[0], msg.get("port"))
                        if peer not in self.peers:
                            self.peers.add(peer)
                            log(f"[P2P] Discovered peer: {msg.get('node_id')} at {addr[0]}")
                except (socket.timeout, json.JSONDecodeError):
                    continue

    def generate_sync_packet(self, data_type: str, payload: dict) -> str:
        packet = {
            "source": self.node_id,
            "type": data_type,
            "payload": payload,
            "timestamp": time.time()
        }
        raw_json = json.dumps(packet)
        encrypted = self.encryption.encrypt(raw_json)
        return base64.b64encode(encrypted).decode()

    def sync_to_all(self, data_type: str, payload: dict):
        packet = self.generate_sync_packet(data_type, payload)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            for peer in self.peers:
                s.sendto(packet.encode(), peer)

    def process_sync_packet(self, b64_packet: str):
        try:
            encrypted = base64.b64decode(b64_packet)
            raw_json = self.encryption.decrypt(encrypted)
            packet = json.loads(raw_json)
            
            log(f"[P2P] Received {packet['type']} sync from {packet['source']}")
            return packet
        except Exception as e:
            log(f"[P2P] Sync failed: {e}")
            return None

    def stop(self):
        self.running = False
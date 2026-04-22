import json
import base64
from sherly.core.encryption import StorageEncryption
from sherly.utils.runtime_utils import log

class P2PSync:
    """
    Handles encrypted P2P state synchronization between Sherly instances.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.encryption = StorageEncryption()

    def generate_sync_packet(self, data_type: str, payload: dict) -> str:
        """
        Long-term vision: P2P State Sync.
        Wraps data in an encrypted packet for transfer.
        """
        packet = {
            "source": self.node_id,
            "type": data_type,
            "payload": payload
        }
        raw_json = json.dumps(packet)
        encrypted = self.encryption.encrypt(raw_json)
        return base64.b64encode(encrypted).decode()

    def process_sync_packet(self, b64_packet: str):
        """
        Decrypts and applies incoming sync data.
        """
        try:
            encrypted = base64.b64decode(b64_packet)
            raw_json = self.encryption.decrypt(encrypted)
            packet = json.loads(raw_json)
            
            log(f"[P2P] Received {packet['type']} sync from {packet['source']}")
            # Logic to merge state would go here
            return packet
        except Exception as e:
            log(f"[P2P] Sync failed: {e}")
            return None

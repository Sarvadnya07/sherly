import socket
import threading
import json
from sherly.utils.runtime_utils import log

class GhostModeServer:
    """
    Long-term vision: IDE 'Ghost' Mode.
    Communicates with IDE plugins via a local socket to provide Zero-UI assistance.
    """
    def __init__(self, port: int = 5555):
        self.port = port
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._run_server, daemon=True)
        thread.start()
        log(f"[Ghost] Server started on port {self.port}")

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', self.port))
            s.listen()
            while self.running:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        request = json.loads(data.decode())
                        log(f"[Ghost] Received request from IDE: {request['command']}")
                        # Process IDE command
                        response = {"status": "ok", "message": f"Processed {request['command']}"}
                        conn.sendall(json.dumps(response).encode())

    def stop(self):
        self.running = False

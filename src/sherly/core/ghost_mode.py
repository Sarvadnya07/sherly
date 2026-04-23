import socket
import threading
import json
from sherly.utils.runtime_utils import log, safe_execute

class GhostModeServer:
    """
    IDE 'Ghost' Mode Server.
    Communicates with IDE plugins via a local socket to provide Zero-UI assistance.
    """
    def __init__(self, port: int = 5555, command_callback=None):
        self.port = port
        self.running = False
        self.command_callback = command_callback

    def start(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._run_server, daemon=True, name="GhostModeServer")
        thread.start()
        log(f"[Ghost] Server started on port {self.port}")

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', self.port))
                s.listen(5)
                s.settimeout(1.0)
                while self.running:
                    try:
                        conn, addr = s.accept()
                        with conn:
                            data = conn.recv(4096)
                            if data:
                                try:
                                    request = json.loads(data.decode())
                                    cmd = request.get("command")
                                    log(f"[Ghost] Received request from IDE: {cmd}")
                                    
                                    response_text = "No callback registered."
                                    if self.command_callback:
                                        response_text = self.command_callback(cmd)
                                        
                                    response = {"status": "ok", "message": response_text}
                                    conn.sendall(json.dumps(response).encode())
                                except json.JSONDecodeError:
                                    conn.sendall(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
                    except socket.timeout:
                        continue
            except Exception as e:
                log(f"[Ghost] Server error: {e}", level="error")
                self.running = False

    def stop(self):
        self.running = False

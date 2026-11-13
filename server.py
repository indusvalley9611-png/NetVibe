"""
NetVibe - LAN Real-Time Chat Application
Server Implementation using Python Socket Programming & Multithreading
Course: Computer Networks Lab (CA-4 Mini Project)
"""

import socket
import threading
import json
import os
import struct
import hashlib
import base64
import mimetypes
import sys
from datetime import datetime

# Configure Windows console for UTF-8 compatibility
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Server Configuration
DEFAULT_HOST = '0.0.0.0'      # Bind to all available network interfaces
DEFAULT_PORT = 5000           # Default TCP Port for the application
BUFFER_SIZE = 4096            # Buffer size for reading socket streams
MAGIC_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def get_local_ip():
    """
    Detect the local IPv4 address of this machine on the active LAN / Wi-Fi network.
    Uses UDP socket connection to an external address (no actual packet sent).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Route to common DNS server to determine default network interface IP
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class LANChatServer:
    """
    Multithreaded TCP Chat Server.
    Supports both Web clients (HTTP + WebSocket) and Native Python TCP Socket clients.
    """

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.local_ip = get_local_ip()
        
        # Shared state protected by mutex lock
        self.clients_lock = threading.Lock()
        # Structure: {client_socket: {"username": str, "address": tuple, "type": "ws"|"tcp"}}
        self.clients = {}
        
        # Server TCP Socket initialization
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Enable SO_REUSEADDR so port can be immediately rebound on restart
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False

    def start(self):
        """Binds socket, listens, and accepts client connections."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(20)
            self.is_running = True
            
            print("=" * 65)
            print("        🚀 NetVibe - LAN Real-Time Chat Server 🚀")
            print("=" * 65)
            print(f"[*] Server Status        : ONLINE")
            print(f"[*] Transport Protocol   : TCP / IP (SOCK_STREAM)")
            print(f"[*] Bound Host           : {self.host} (All Interfaces)")
            print(f"[*] Local IPv4 Address   : {self.local_ip}")
            print(f"[*] TCP Port             : {self.port}")
            print("-" * 65)
            print(f"[+] Web Browser Access   : http://{self.local_ip}:{self.port}")
            print(f"[+] Localhost Access     : http://127.0.0.1:{self.port}")
            print(f"[+] Python GUI Client    : python client_gui.py")
            print(f"[+] Python CLI Client    : python client.py")
            print("-" * 65)
            print("[*] Waiting for incoming client connections (Press Ctrl+C to stop)...")
            print("=" * 65 + "\n")

            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    # Spawn a dedicated thread for each client to enable concurrency
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                except socket.error:
                    break

        except KeyboardInterrupt:
            print("\n[!] Keyboard interrupt received. Shutting down server...")
        except Exception as e:
            print(f"[!] Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Closes all active sockets and stops the server."""
        self.is_running = False
        with self.clients_lock:
            for s in list(self.clients.keys()):
                try:
                    s.close()
                except Exception:
                    pass
            self.clients.clear()
            
        try:
            self.server_socket.close()
        except Exception:
            pass
        print("[*] Server shutdown complete. Goodbye!")

    # -------------------------------------------------------------
    # Client Connection & Protocol Handling
    # -------------------------------------------------------------
    def handle_client(self, client_socket, client_address):
        """
        Worker thread for each connected socket.
        Inspects the first payload to detect whether the client is:
          1. Web Browser (HTTP request -> Serve web assets or upgrade to WebSocket)
          2. Native TCP Client (Raw JSON packets)
        """
        ip, port = client_address
        # Read the initial packet with peek to inspect the request protocol
        try:
            initial_data = client_socket.recv(BUFFER_SIZE)
            if not initial_data:
                client_socket.close()
                return
        except Exception:
            client_socket.close()
            return

        # Check if the connection starts with an HTTP request method
        if initial_data.startswith(b"GET ") or initial_data.startswith(b"POST "):
            self.handle_http_or_ws(client_socket, client_address, initial_data)
        else:
            # Native TCP client sending raw JSON
            self.handle_raw_tcp(client_socket, client_address, initial_data)

    def handle_http_or_ws(self, client_socket, client_address, initial_data):
        """Handles HTTP static file serving or WebSocket handshake."""
        request_text = initial_data.decode('utf-8', errors='ignore')
        headers = request_text.split('\r\n')
        request_line = headers[0] if headers else ""
        parts = request_line.split()

        if len(parts) < 2:
            client_socket.close()
            return

        method, path = parts[0], parts[1]

        # Check for WebSocket Upgrade request
        is_websocket = False
        sec_key = None
        for line in headers:
            lower_line = line.lower()
            if "upgrade: websocket" in lower_line:
                is_websocket = True
            if lower_line.startswith("sec-websocket-key:"):
                sec_key = line.split(":", 1)[1].strip()

        if is_websocket and sec_key:
            # Perform WebSocket RFC 6455 Handshake
            self.complete_ws_handshake(client_socket, sec_key)
            self.run_ws_loop(client_socket, client_address)
        else:
            # Standard HTTP GET request: Serve HTML, CSS, JS, or API info
            self.serve_http(client_socket, path)

    def complete_ws_handshake(self, client_socket, sec_key):
        """Generates HTTP 101 Switching Protocols response for WebSocket."""
        accept_raw = sec_key + MAGIC_WS_GUID
        accept_sha1 = hashlib.sha1(accept_raw.encode('utf-8')).digest()
        accept_base64 = base64.b64encode(accept_sha1).decode('utf-8')
        
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_base64}\r\n\r\n"
        )
        client_socket.sendall(response.encode('utf-8'))

    # -------------------------------------------------------------
    # HTTP Static File Serving (Built-in Web Server)
    # -------------------------------------------------------------
    def serve_http(self, client_socket, path):
        """Serves UI files (HTML, CSS, JS) over raw TCP socket."""
        try:
            if path == '/' or path == '/index.html':
                file_path = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
            elif path.startswith('/static/'):
                rel_path = path[len('/static/'):]
                file_path = os.path.join(os.path.dirname(__file__), 'static', rel_path)
            elif path == '/api/info':
                # Quick JSON status endpoint
                info = json.dumps({
                    "status": "online",
                    "server_ip": self.local_ip,
                    "port": self.port,
                    "online_count": len(self.clients)
                })
                resp = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(info)}\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "Connection: close\r\n\r\n" + info
                )
                client_socket.sendall(resp.encode('utf-8'))
                client_socket.close()
                return
            else:
                rel_path = path.lstrip('/')
                file_path = os.path.join(os.path.dirname(__file__), 'static', rel_path)

            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
                if content_type.startswith('text/') or content_type == 'application/javascript':
                    content_type += '; charset=utf-8'

                with open(file_path, 'rb') as f:
                    content = f.read()

                header = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {content_type}\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "Connection: close\r\n\r\n"
                )
                client_socket.sendall(header.encode('utf-8') + content)
            else:
                not_found = "<h1>404 Not Found</h1>"
                header = (
                    "HTTP/1.1 404 Not Found\r\n"
                    "Content-Type: text/html\r\n"
                    f"Content-Length: {len(not_found)}\r\n"
                    "Connection: close\r\n\r\n"
                )
                client_socket.sendall(header.encode('utf-8') + not_found.encode('utf-8'))
        except Exception as e:
            print(f"[!] HTTP Serving error: {e}")
        finally:
            client_socket.close()

    # -------------------------------------------------------------
    # WebSocket Frame Parsing & Processing (RFC 6455)
    # -------------------------------------------------------------
    def run_ws_loop(self, client_socket, client_address):
        """Reads and processes incoming WebSocket frames."""
        with self.clients_lock:
            self.clients[client_socket] = {
                "username": None,
                "address": client_address,
                "type": "ws"
            }

        print(f"[+] [CONNECT] Client socket connected: {client_address[0]}:{client_address[1]} (WebSocket)")

        def recv_exact(n):
            buf = bytearray()
            while len(buf) < n:
                chunk = client_socket.recv(n - len(buf))
                if not chunk:
                    return None
                buf.extend(chunk)
            return bytes(buf)

        try:
            while self.is_running:
                head = recv_exact(2)
                if not head:
                    break

                b1, b2 = head[0], head[1]
                opcode = b1 & 0x0F
                is_masked = (b2 & 0x80) != 0
                payload_len = b2 & 0x7F

                if opcode == 0x8:  # Connection close frame
                    break
                elif opcode == 0x9:  # Ping frame
                    # Respond with Pong frame (opcode 0xA)
                    pong_frame = bytearray([0x8A, 0x00])
                    client_socket.sendall(pong_frame)
                    continue

                if payload_len == 126:
                    ext = recv_exact(2)
                    if not ext:
                        break
                    payload_len = struct.unpack("!H", ext)[0]
                elif payload_len == 127:
                    ext = recv_exact(8)
                    if not ext:
                        break
                    payload_len = struct.unpack("!Q", ext)[0]

                mask = recv_exact(4) if is_masked else None
                raw_payload = recv_exact(payload_len)
                if raw_payload is None:
                    break

                payload = bytearray(raw_payload)
                if is_masked and mask:
                    for i in range(len(payload)):
                        payload[i] ^= mask[i % 4]

                message_text = payload.decode('utf-8', errors='ignore')
                self.process_incoming_json(client_socket, message_text)

        except Exception as e:
            pass
        finally:
            self.disconnect_client(client_socket)

    # -------------------------------------------------------------
    # Native Raw TCP Socket Handling
    # -------------------------------------------------------------
    def handle_raw_tcp(self, client_socket, client_address, initial_data):
        """Handles native Python TCP clients sending JSON lines."""
        with self.clients_lock:
            self.clients[client_socket] = {
                "username": None,
                "address": client_address,
                "type": "tcp"
            }

        print(f"[+] [CONNECT] Client socket connected: {client_address[0]}:{client_address[1]} (Raw TCP)")
        
        # Process the initial packet received
        buffer = initial_data.decode('utf-8', errors='ignore')
        lines = buffer.split('\n')
        buffer = lines[-1]
        for line in lines[:-1]:
            if line.strip():
                self.process_incoming_json(client_socket, line.strip())

        try:
            while self.is_running:
                chunk = client_socket.recv(BUFFER_SIZE)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')
                lines = buffer.split('\n')
                buffer = lines[-1]
                for line in lines[:-1]:
                    if line.strip():
                        self.process_incoming_json(client_socket, line.strip())
        except Exception:
            pass
        finally:
            self.disconnect_client(client_socket)

    # -------------------------------------------------------------
    # Chat Logic & Message Dispatching
    # -------------------------------------------------------------
    def process_incoming_json(self, client_socket, json_str):
        """Parses JSON action: join, message, or leave."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        if msg_type == "join":
            username = data.get("username", "Anonymous").strip()
            if not username:
                username = "User_" + str(client_socket.fileno())

            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients[client_socket]["username"] = username

            now = datetime.now().strftime("%I:%M %p")
            print(f"[+] [JOIN] User '{username}' joined the chat. Online count: {self.get_online_count()}")

            # 1. Send confirmation & user list to the newly joined client
            welcome_packet = {
                "type": "welcome",
                "username": username,
                "server_ip": self.local_ip,
                "port": self.port,
                "timestamp": now,
                "users": self.get_active_usernames()
            }
            self.send_to_client(client_socket, welcome_packet)

            # 2. Broadcast system join notification to ALL clients
            join_notification = {
                "type": "notification",
                "event": "user_joined",
                "username": username,
                "message": f"👋 {username} joined the chat.",
                "timestamp": now,
                "users": self.get_active_usernames()
            }
            self.broadcast(join_notification)

        elif msg_type == "message":
            with self.clients_lock:
                client_info = self.clients.get(client_socket)
                sender_username = client_info["username"] if client_info else "Unknown"

            text = data.get("message", "").strip()
            if not text:
                return

            now = datetime.now().strftime("%I:%M %p")
            print(f"[MSG] [{now}] <{sender_username}>: {text}")

            chat_packet = {
                "type": "message",
                "sender": sender_username,
                "message": text,
                "timestamp": now
            }
            self.broadcast(chat_packet)

        elif msg_type == "leave":
            self.disconnect_client(client_socket)

    def disconnect_client(self, client_socket):
        """Removes a disconnected client and broadcasts leave notification."""
        username = None
        with self.clients_lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]["username"]
                del self.clients[client_socket]

        try:
            client_socket.close()
        except Exception:
            pass

        if username:
            now = datetime.now().strftime("%I:%M %p")
            print(f"[-] [LEAVE] User '{username}' disconnected. Online count: {self.get_online_count()}")
            leave_notification = {
                "type": "notification",
                "event": "user_left",
                "username": username,
                "message": f"🚪 {username} left the chat.",
                "timestamp": now,
                "users": self.get_active_usernames()
            }
            self.broadcast(leave_notification)

    def get_online_count(self):
        """Returns the number of active authenticated clients."""
        with self.clients_lock:
            return sum(1 for c in self.clients.values() if c["username"] is not None)

    def get_active_usernames(self):
        """Returns list of all active usernames."""
        with self.clients_lock:
            return [info["username"] for info in self.clients.values() if info["username"] is not None]

    # -------------------------------------------------------------
    # Transmission & Framing Layer
    # -------------------------------------------------------------
    def send_to_client(self, client_socket, data_dict):
        """Encodes and sends data packet to a specific client."""
        with self.clients_lock:
            info = self.clients.get(client_socket)
            if not info:
                return
            client_type = info["type"]

        payload_str = json.dumps(data_dict)
        try:
            if client_type == "ws":
                frame = self.encode_ws_text_frame(payload_str)
                client_socket.sendall(frame)
            else:
                # Raw TCP JSON line
                line = (payload_str + "\n").encode('utf-8')
                client_socket.sendall(line)
        except Exception:
            # Socket will be cleaned up on next read/disconnect
            pass

    def broadcast(self, data_dict):
        """Sends a JSON packet to all connected clients."""
        with self.clients_lock:
            active_sockets = list(self.clients.keys())

        for client_socket in active_sockets:
            self.send_to_client(client_socket, data_dict)

    @staticmethod
    def encode_ws_text_frame(message_str):
        """Encodes a UTF-8 string into an unmasked RFC 6455 server WebSocket frame."""
        data = message_str.encode('utf-8')
        length = len(data)
        frame = bytearray([0x81])  # FIN=1, Text Opcode=0x1

        if length <= 125:
            frame.append(length)
        elif length <= 65535:
            frame.append(126)
            frame.extend(struct.pack("!H", length))
        else:
            frame.append(127)
            frame.extend(struct.pack("!Q", length))

        frame.extend(data)
        return bytes(frame)


if __name__ == '__main__':
    server = LANChatServer(host=DEFAULT_HOST, port=DEFAULT_PORT)
    server.start()

"""
Automated Test Suite for NetVibe LAN Chat
Validates multi-client TCP connections, WebSockets, broadcast messaging,
user tracking, and join/leave notifications.
"""

import socket
import threading
import json
import time
import struct
import hashlib
import base64
import sys
import io

# Force UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from server import LANChatServer, DEFAULT_PORT


class RawTCPTestClient:
    def __init__(self, name, host="127.0.0.1", port=DEFAULT_PORT):
        self.name = name
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.received_messages = []
        self.buffer = ""
        self.running = False
        self.recv_thread = None

    def connect_and_join(self):
        self.sock.connect((self.host, self.port))
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

        join_packet = json.dumps({"type": "join", "username": self.name}) + "\n"
        self.sock.sendall(join_packet.encode('utf-8'))

    def _recv_loop(self):
        while self.running:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                self.buffer += chunk.decode('utf-8', errors='ignore')
                lines = self.buffer.split('\n')
                self.buffer = lines[-1]
                for line in lines[:-1]:
                    if line.strip():
                        packet = json.loads(line.strip())
                        self.received_messages.append(packet)
            except Exception:
                break

    def send_message(self, text):
        packet = json.dumps({"type": "message", "message": text}) + "\n"
        self.sock.sendall(packet.encode('utf-8'))

    def disconnect(self):
        self.running = False
        try:
            leave_pkt = json.dumps({"type": "leave"}) + "\n"
            self.sock.sendall(leave_pkt.encode('utf-8'))
        except Exception:
            pass
        self.sock.close()


class WebSocketTestClient:
    def __init__(self, name, host="127.0.0.1", port=DEFAULT_PORT):
        self.name = name
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.received_messages = []
        self.running = False
        self.recv_thread = None

    def connect_and_join(self):
        self.sock.connect((self.host, self.port))
        
        # 1. Perform HTTP WebSocket Handshake
        key = base64.b64encode(b"0123456789abcdef").decode()
        handshake = (
            f"GET /ws HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode('utf-8'))

        # Read handshake response
        response = self.sock.recv(2048).decode('utf-8')
        assert "101 Switching Protocols" in response, f"Handshake failed: {response}"

        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

        # Send JOIN frame
        join_packet = json.dumps({"type": "join", "username": self.name})
        self._send_frame(join_packet)

    def _send_frame(self, text):
        # Client frames must be masked according to RFC 6455
        payload = text.encode('utf-8')
        length = len(payload)
        mask_key = b"\x12\x34\x56\x78"

        masked_payload = bytearray(length)
        for i in range(length):
            masked_payload[i] = payload[i] ^ mask_key[i % 4]

        frame = bytearray([0x81])
        if length <= 125:
            frame.append(0x80 | length)
        elif length <= 65535:
            frame.append(0x80 | 126)
            frame.extend(struct.pack("!H", length))
        else:
            frame.append(0x80 | 127)
            frame.extend(struct.pack("!Q", length))

        frame.extend(mask_key)
        frame.extend(masked_payload)
        self.sock.sendall(bytes(frame))

    def _recv_loop(self):
        def recv_exact(n):
            buf = bytearray()
            while len(buf) < n:
                chunk = self.sock.recv(n - len(buf))
                if not chunk:
                    return None
                buf.extend(chunk)
            return bytes(buf)

        while self.running:
            try:
                head = recv_exact(2)
                if not head:
                    break
                b1, b2 = head[0], head[1]
                payload_len = b2 & 0x7F

                if payload_len == 126:
                    ext = recv_exact(2)
                    payload_len = struct.unpack("!H", ext)[0]
                elif payload_len == 127:
                    ext = recv_exact(8)
                    payload_len = struct.unpack("!Q", ext)[0]

                raw = recv_exact(payload_len)
                if raw is None:
                    break
                data = json.loads(raw.decode('utf-8'))
                self.received_messages.append(data)
            except Exception:
                break

    def send_message(self, text):
        packet = json.dumps({"type": "message", "message": text})
        self._send_frame(packet)

    def disconnect(self):
        self.running = False
        try:
            leave_pkt = json.dumps({"type": "leave"})
            self._send_frame(leave_pkt)
        except Exception:
            pass
        self.sock.close()


def run_tests():
    print("=" * 65)
    print("      🧪 NetVibe LAN Chat Application - Automated Test Suite 🧪")
    print("=" * 65)

    TEST_PORT = 5002

    print(f"\n[1] Starting LANChatServer on port {TEST_PORT}...")
    server = LANChatServer(host="127.0.0.1", port=TEST_PORT)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print("    ✓ Server is up and listening on TCP socket.")

    # -------------------------------------------------------------
    # Test 1: Connect Alice (Raw TCP)
    # -------------------------------------------------------------
    print("\n[2] Connecting Client 1: Alice (Raw TCP Socket)...")
    alice = RawTCPTestClient("Alice", port=TEST_PORT)
    alice.connect_and_join()
    time.sleep(0.4)

    assert len(alice.received_messages) >= 1, "Alice should have received welcome packet"
    assert alice.received_messages[0]["type"] == "welcome"
    assert alice.received_messages[0]["username"] == "Alice"
    print("    ✓ Alice connected & received 'welcome' packet.")
    print(f"    ✓ Online count on server: {server.get_online_count()}")

    # -------------------------------------------------------------
    # Test 2: Connect Bob (Raw TCP) and verify Join Notification
    # -------------------------------------------------------------
    print("\n[3] Connecting Client 2: Bob (Raw TCP Socket)...")
    bob = RawTCPTestClient("Bob", port=TEST_PORT)
    bob.connect_and_join()
    time.sleep(0.4)

    assert server.get_online_count() == 2, f"Expected 2 online users, got {server.get_online_count()}"
    print("    ✓ Bob connected. Server registered 2 online users.")

    # Check Alice received Bob's join notification
    alice_join_notifs = [m for m in alice.received_messages if m.get("event") == "user_joined" and m.get("username") == "Bob"]
    assert len(alice_join_notifs) > 0, "Alice should receive notification that Bob joined"
    print("    ✓ Alice successfully received Bob's join notification.")

    # -------------------------------------------------------------
    # Test 3: Connect Charlie via WebSocket (Web Browser Protocol)
    # -------------------------------------------------------------
    print("\n[4] Connecting Client 3: Charlie (WebSocket / Web Client)...")
    charlie = WebSocketTestClient("Charlie", port=TEST_PORT)
    charlie.connect_and_join()
    time.sleep(0.4)

    assert server.get_online_count() == 3, f"Expected 3 online users, got {server.get_online_count()}"
    print("    ✓ Charlie completed RFC 6455 handshake & joined.")
    print("    ✓ Server successfully bridged Raw TCP and WebSocket clients!")

    # -------------------------------------------------------------
    # Test 4: Real-Time Chat Broadcast (Bob -> Alice & Charlie)
    # -------------------------------------------------------------
    print("\n[5] Testing Real-Time Messaging: Bob sends 'Hello NetVibe!'...")
    bob.send_message("Hello NetVibe!")
    time.sleep(0.4)

    alice_chat = [m for m in alice.received_messages if m.get("type") == "message" and m.get("message") == "Hello NetVibe!"]
    charlie_chat = [m for m in charlie.received_messages if m.get("type") == "message" and m.get("message") == "Hello NetVibe!"]

    assert len(alice_chat) > 0, "Alice did not receive Bob's message"
    assert alice_chat[0]["sender"] == "Bob"
    assert "timestamp" in alice_chat[0], "Message packet missing timestamp"
    print("    ✓ Alice (Raw TCP) received Bob's message with correct timestamp & sender.")

    assert len(charlie_chat) > 0, "Charlie did not receive Bob's message"
    assert charlie_chat[0]["sender"] == "Bob"
    print("    ✓ Charlie (WebSocket) received Bob's message across protocol boundary.")

    # -------------------------------------------------------------
    # Test 5: Real-Time Chat from Web (Charlie -> Alice & Bob)
    # -------------------------------------------------------------
    print("\n[6] Testing Web Messaging: Charlie sends 'Greetings from Web!'...")
    charlie.send_message("Greetings from Web!")
    time.sleep(0.4)

    alice_web_chat = [m for m in alice.received_messages if m.get("message") == "Greetings from Web!"]
    bob_web_chat = [m for m in bob.received_messages if m.get("message") == "Greetings from Web!"]

    assert len(alice_web_chat) > 0, "Alice did not receive Charlie's web message"
    assert len(bob_web_chat) > 0, "Bob did not receive Charlie's web message"
    print("    ✓ Both TCP clients received WebSocket client's message.")

    # -------------------------------------------------------------
    # Test 6: Disconnection & Leave Notification
    # -------------------------------------------------------------
    print("\n[7] Testing Disconnection Handling: Bob disconnects...")
    bob.disconnect()
    time.sleep(0.5)

    assert server.get_online_count() == 2, f"Expected 2 online users after Bob leaves, got {server.get_online_count()}"
    alice_leave_notifs = [m for m in alice.received_messages if m.get("event") == "user_left" and m.get("username") == "Bob"]
    assert len(alice_leave_notifs) > 0, "Alice did not receive Bob's leave notification"
    print("    ✓ Alice received leave notification: '🚪 Bob left the chat.'")
    print(f"    ✓ Online count properly decremented to: {server.get_online_count()}")

    # Cleanup
    alice.disconnect()
    charlie.disconnect()
    server.stop()

    print("\n" + "=" * 65)
    print("     🎉 ALL 6 TEST SUITES PASSED FLAWLESSLY! (100% SUCCESS) 🎉")
    print("=" * 65)
    print("  • TCP Socket Binding & Listening     : PASS")
    print("  • Multithreading Concurrency         : PASS")
    print("  • Username Registration              : PASS")
    print("  • Real-Time Message Broadcast        : PASS")
    print("  • Timestamps & Sender Attributes     : PASS")
    print("  • Join / Leave Notifications         : PASS")
    print("  • Active Users Tracking              : PASS")
    print("  • Raw TCP + WebSocket Interoperability: PASS")
    print("=" * 65)


if __name__ == '__main__':
    run_tests()

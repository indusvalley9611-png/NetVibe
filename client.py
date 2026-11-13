"""
NetVibe - Python Terminal / CLI Client
Interactive Command-Line TCP Socket Client
Course: Computer Networks Lab (CA-4 Mini Project)
"""

import socket
import threading
import json
import sys
from datetime import datetime

# Configure Windows console for UTF-8 compatibility
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ANSI Color Codes for terminal output
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_MAGENTA = "\033[95m"
COLOR_DIM = "\033[2m"


def receive_handler(client_socket, my_username):
    """Background thread to read and print incoming server messages."""
    buffer = ""
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                print(f"\n{COLOR_RED}[!] Server closed connection.{COLOR_RESET}")
                break
            buffer += data.decode('utf-8', errors='ignore')
            lines = buffer.split('\n')
            buffer = lines[-1]
            for line in lines[:-1]:
                if not line.strip():
                    continue
                try:
                    packet = json.loads(line.strip())
                except Exception:
                    continue

                msg_type = packet.get("type")
                if msg_type == "welcome":
                    users = ", ".join(packet.get("users", []))
                    print(f"{COLOR_GREEN}[✓] Joined successfully! Online users: [{users}]{COLOR_RESET}")
                elif msg_type == "notification":
                    print(f"\n{COLOR_YELLOW}[*] {packet.get('message', '')}{COLOR_RESET}")
                    print(f"{COLOR_CYAN}> {COLOR_RESET}", end="", flush=True)
                elif msg_type == "message":
                    sender = packet.get("sender", "Unknown")
                    text = packet.get("message", "")
                    ts = packet.get("timestamp", "")
                    if sender != my_username:
                        print(f"\n{COLOR_MAGENTA}[{ts}] <{sender}>{COLOR_RESET}: {text}")
                        print(f"{COLOR_CYAN}> {COLOR_RESET}", end="", flush=True)
        except Exception:
            break

    print(f"\n{COLOR_RED}[!] Disconnected from server. Press Enter to exit.{COLOR_RESET}")
    client_socket.close()


def main():
    print(f"{COLOR_BOLD}{COLOR_CYAN}")
    print("=" * 60)
    print("       NetVibe - LAN Chat Terminal Client       ")
    print("=" * 60 + f"{COLOR_RESET}")

    default_host = "127.0.0.1"
    default_port = 5000

    host = input(f"Enter Server IPv4 Address [{default_host}]: ").strip() or default_host
    port_input = input(f"Enter TCP Port [{default_port}]: ").strip() or str(default_port)
    try:
        port = int(port_input)
    except ValueError:
        print(f"{COLOR_RED}[!] Invalid port number.{COLOR_RESET}")
        return

    username = input("Enter your username: ").strip()
    while not username:
        username = input("Username cannot be empty. Enter username: ").strip()

    print(f"\n[*] Connecting to TCP Socket {host}:{port}...")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
    except Exception as e:
        print(f"{COLOR_RED}[!] Connection failed: {e}{COLOR_RESET}")
        return

    # Send JOIN
    join_packet = json.dumps({"type": "join", "username": username}) + "\n"
    s.sendall(join_packet.encode('utf-8'))

    # Start receive thread
    t = threading.Thread(target=receive_handler, args=(s, username), daemon=True)
    t.start()

    print(f"{COLOR_GREEN}[+] Connected! Type your message and press Enter.")
    print(f"[*] Type '/quit' to leave the chat room.{COLOR_RESET}\n")

    try:
        while True:
            msg = input(f"{COLOR_CYAN}> {COLOR_RESET}").strip()
            if not msg:
                continue
            if msg.lower() == "/quit":
                leave_packet = json.dumps({"type": "leave"}) + "\n"
                try:
                    s.sendall(leave_packet.encode('utf-8'))
                except Exception:
                    pass
                break
            
            chat_packet = json.dumps({"type": "message", "message": msg}) + "\n"
            s.sendall(chat_packet.encode('utf-8'))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass
        print(f"\n{COLOR_YELLOW}[*] You have exited the chat room.{COLOR_RESET}")


if __name__ == '__main__':
    main()

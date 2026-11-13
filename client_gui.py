"""
NetVibe - Python Desktop GUI Client
Built with Tkinter and Python Socket Programming
Course: Computer Networks Lab (CA-4 Mini Project)
"""

import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# GUI Theme Colors (Catppuccin Mocha / Slate Dark Mode)
BG_DARK = "#111827"
BG_CARD = "#1f2937"
BG_INPUT = "#374151"
ACCENT_COLOR = "#6366f1"
TEXT_COLOR = "#f9fafb"
TEXT_MUTED = "#9ca3af"
SUCCESS_COLOR = "#10b981"
DANGER_COLOR = "#ef4444"


class NetVibeClientGUI:
    def __init__(self):
        self.client_socket = None
        self.username = ""
        self.server_ip = "127.0.0.1"
        self.server_port = 5000
        self.is_connected = False
        self.receive_thread = None

        # Build Main Window
        self.root = tk.Tk()
        self.root.title("NetVibe - LAN Chat Desktop Client")
        self.root.geometry("880x620")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_DARK)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Show Login Screen first
        self.show_login_dialog()

    # -------------------------------------------------------------
    # 1. LOGIN / CONNECT DIALOG
    # -------------------------------------------------------------
    def show_login_dialog(self):
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Join NetVibe LAN Chat")
        self.login_window.geometry("400x420")
        self.login_window.resizable(False, False)
        self.login_window.configure(bg=BG_DARK)
        self.login_window.transient(self.root)
        self.login_window.grab_set()

        # Center on parent
        self.login_window.eval('tk::PlaceWindow %s center' % self.login_window.winfo_toplevel())

        # Header Title
        lbl_title = tk.Label(
            self.login_window, 
            text="NetVibe LAN Chat", 
            font=("Arial", 18, "bold"),
            fg="#ffffff", 
            bg=BG_DARK
        )
        lbl_title.pack(pady=(24, 4))

        lbl_sub = tk.Label(
            self.login_window, 
            text="TCP/IP Socket Programming • Port 5000", 
            font=("Arial", 10),
            fg=TEXT_MUTED, 
            bg=BG_DARK
        )
        lbl_sub.pack(pady=(0, 20))

        frame = tk.Frame(self.login_window, bg=BG_DARK)
        frame.pack(padx=30, fill=tk.X)

        # Username
        tk.Label(frame, text="Username:", font=("Arial", 11, "bold"), fg=TEXT_COLOR, bg=BG_DARK).pack(anchor=tk.W)
        self.ent_username = tk.Entry(frame, font=("Arial", 12), bg=BG_INPUT, fg="#ffffff", insertbackground="#fff", relief=tk.FLAT)
        self.ent_username.pack(fill=tk.X, pady=(4, 14), ipady=6)
        self.ent_username.insert(0, "Student_Client")
        self.ent_username.focus()

        # Server IP
        tk.Label(frame, text="Server IPv4 Address:", font=("Arial", 11, "bold"), fg=TEXT_COLOR, bg=BG_DARK).pack(anchor=tk.W)
        self.ent_ip = tk.Entry(frame, font=("Arial", 12), bg=BG_INPUT, fg="#ffffff", insertbackground="#fff", relief=tk.FLAT)
        self.ent_ip.pack(fill=tk.X, pady=(4, 14), ipady=6)
        self.ent_ip.insert(0, "127.0.0.1")

        # Server Port
        tk.Label(frame, text="TCP Port:", font=("Arial", 11, "bold"), fg=TEXT_COLOR, bg=BG_DARK).pack(anchor=tk.W)
        self.ent_port = tk.Entry(frame, font=("Arial", 12), bg=BG_INPUT, fg="#ffffff", insertbackground="#fff", relief=tk.FLAT)
        self.ent_port.pack(fill=tk.X, pady=(4, 20), ipady=6)
        self.ent_port.insert(0, "5000")

        # Connect Button
        btn_connect = tk.Button(
            self.login_window, 
            text="Connect to LAN Server", 
            font=("Arial", 12, "bold"),
            bg=ACCENT_COLOR, 
            fg="#ffffff", 
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief=tk.FLAT, 
            cursor="hand2",
            command=self.attempt_connect
        )
        btn_connect.pack(padx=30, fill=tk.X, ipady=8)

        # Allow pressing Enter to connect
        self.login_window.bind("<Return>", lambda event: self.attempt_connect())

    def attempt_connect(self):
        username = self.ent_username.get().strip()
        ip = self.ent_ip.get().strip()
        port_str = self.ent_port.get().strip()

        if not username:
            messagebox.showerror("Validation Error", "Please enter a valid username.", parent=self.login_window)
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Port must be an integer.", parent=self.login_window)
            return

        self.username = username
        self.server_ip = ip
        self.server_port = port

        # Establish TCP Socket Connection
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0)
            self.client_socket.connect((self.server_ip, self.server_port))
            self.client_socket.settimeout(None)
            self.is_connected = True

            # Send JOIN message
            join_msg = json.dumps({"type": "join", "username": self.username}) + "\n"
            self.client_socket.sendall(join_msg.encode('utf-8'))

            # Close login dialog
            self.login_window.destroy()

            # Build main chat interface
            self.build_chat_ui()

            # Start background thread to listen for incoming TCP packets
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()

        except Exception as e:
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect to {self.server_ip}:{self.server_port}\nError: {e}\n\n"
                f"Ensure server.py is running on the host machine and firewall allows TCP port 5000.",
                parent=self.login_window
            )

    # -------------------------------------------------------------
    # 2. MAIN CHAT DASHBOARD
    # -------------------------------------------------------------
    def build_chat_ui(self):
        # Top Header Bar
        top_bar = tk.Frame(self.root, bg=BG_CARD, height=60, padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        lbl_room = tk.Label(
            top_bar, 
            text="🌐 NetVibe LAN Chat  |  General Room", 
            font=("Arial", 14, "bold"), 
            fg="#ffffff", 
            bg=BG_CARD
        )
        lbl_room.pack(side=tk.LEFT)

        self.lbl_status = tk.Label(
            top_bar, 
            text=f"🟢 Connected ({self.server_ip}:{self.server_port}) as {self.username}", 
            font=("Arial", 11), 
            fg=SUCCESS_COLOR, 
            bg=BG_CARD
        )
        self.lbl_status.pack(side=tk.RIGHT)

        # Body Layout: Sidebar (Users) + Main Chat Area
        body_frame = tk.Frame(self.root, bg=BG_DARK)
        body_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Sidebar
        sidebar = tk.Frame(body_frame, bg=BG_CARD, width=220, padx=12, pady=12)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="ONLINE USERS", font=("Arial", 11, "bold"), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 8))

        self.user_listbox = tk.Listbox(
            sidebar, 
            bg=BG_INPUT, 
            fg=TEXT_COLOR, 
            selectbackground=ACCENT_COLOR,
            relief=tk.FLAT, 
            font=("Arial", 11),
            bd=0,
            highlightthickness=0
        )
        self.user_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        btn_leave = tk.Button(
            sidebar, 
            text="Disconnect", 
            font=("Arial", 10, "bold"),
            bg=DANGER_COLOR, 
            fg="#ffffff", 
            relief=tk.FLAT,
            cursor="hand2",
            command=self.on_close
        )
        btn_leave.pack(fill=tk.X, ipady=4)

        # Main Chat Area
        chat_container = tk.Frame(body_frame, bg=BG_DARK)
        chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, 
            wrap=tk.WORD, 
            bg=BG_CARD, 
            fg=TEXT_COLOR,
            font=("Segoe UI", 11), 
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=16,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        # Tag configurations for rich message coloring
        self.chat_display.tag_config("time", foreground=TEXT_MUTED, font=("Segoe UI", 9))
        self.chat_display.tag_config("system", foreground="#fbbf24", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_config("sender_me", foreground="#818cf8", font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_config("sender_other", foreground="#34d399", font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_config("message", foreground="#f3f4f6", font=("Segoe UI", 11))

        # Input Bar
        input_bar = tk.Frame(chat_container, bg=BG_DARK)
        input_bar.pack(fill=tk.X)

        self.msg_entry = tk.Entry(
            input_bar, 
            font=("Segoe UI", 12), 
            bg=BG_INPUT, 
            fg="#ffffff", 
            insertbackground="#fff", 
            relief=tk.FLAT
        )
        self.msg_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_message())
        self.msg_entry.focus()

        btn_send = tk.Button(
            input_bar, 
            text="Send  ➤", 
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_COLOR, 
            fg="#ffffff", 
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief=tk.FLAT, 
            cursor="hand2",
            padx=20,
            command=self.send_message
        )
        btn_send.pack(side=tk.RIGHT, ipady=6)

    # -------------------------------------------------------------
    # 3. MESSAGE TRANSMISSION & RECEIVING (TCP SOCKETS)
    # -------------------------------------------------------------
    def send_message(self):
        text = self.msg_entry.get().strip()
        if not text or not self.is_connected:
            return

        try:
            packet = json.dumps({"type": "message", "message": text}) + "\n"
            self.client_socket.sendall(packet.encode('utf-8'))
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            self.append_text(f"[!] Send failed: {e}\n", "system")

    def receive_messages(self):
        """Continuously reads TCP stream chunks from server."""
        buffer = ""
        while self.is_connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8', errors='ignore')
                lines = buffer.split('\n')
                buffer = lines[-1]
                for line in lines[:-1]:
                    if line.strip():
                        self.root.after(0, self.process_server_packet, line.strip())
            except Exception:
                break

        self.is_connected = False
        self.root.after(0, self.handle_disconnect)

    def process_server_packet(self, json_str):
        try:
            packet = json.loads(json_str)
        except Exception:
            return

        msg_type = packet.get("type")

        if msg_type in ("welcome", "notification"):
            users = packet.get("users", [])
            self.update_user_list(users)
            if "message" in packet:
                self.append_text(f"[{packet.get('timestamp', '')}] {packet['message']}\n", "system")

        elif msg_type == "message":
            sender = packet.get("sender", "Unknown")
            text = packet.get("message", "")
            timestamp = packet.get("timestamp", "")
            is_me = (sender == self.username)

            tag_sender = "sender_me" if is_me else "sender_other"
            sender_display = "You" if is_me else sender

            self.append_text(f"[{timestamp}] ", "time")
            self.append_text(f"{sender_display}: ", tag_sender)
            self.append_text(f"{text}\n\n", "message")

    def update_user_list(self, users):
        self.user_listbox.delete(0, tk.END)
        for u in users:
            prefix = "● " if u != self.username else "★ "
            suffix = " (You)" if u == self.username else ""
            self.user_listbox.insert(tk.END, f"{prefix}{u}{suffix}")

    def append_text(self, text, tag):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text, tag)
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)

    def handle_disconnect(self):
        if hasattr(self, 'lbl_status'):
            self.lbl_status.config(text="🔴 Disconnected from server", fg=DANGER_COLOR)
        self.append_text("[!] You have been disconnected from the server.\n", "system")

    def on_close(self):
        self.is_connected = False
        if self.client_socket:
            try:
                leave_msg = json.dumps({"type": "leave"}) + "\n"
                self.client_socket.sendall(leave_msg.encode('utf-8'))
                self.client_socket.close()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = NetVibeClientGUI()
    app.run()

# Laboratory Project Report: Continuous Assessment (CA-4)

# LAN-Based Real-Time Chat Application Using Python Socket Programming

**Course Title:** Computer Networks Laboratory  
**Course Code:** CS-3104 / CN-LAB  
**Evaluation:** Continuous Assessment 4 (Mini-Project - 20 Marks)  
**Academic Session:** 2026–2027  

---

## Executive Summary / Abstract

Real-time communication across interconnected computing devices represents one of the foundational paradigms of modern computer networking. This project presents **NetVibe**, a robust, educational, and production-grade Local Area Network (LAN) messaging system developed using Python 3 socket programming and TCP/IP protocol principles. 

The application utilizes a centralized **Client-Server Architecture** operating over Transmission Control Protocol (TCP) port 5000. To eliminate the blocking nature of synchronous I/O operations and support concurrent peer communication, the server leverages **Multithreading** (`threading` module), spawning a dedicated worker thread per connected client socket. 

To bridge textbook network programming with contemporary human-computer interaction, the application features a unified dual-protocol engine supporting:
1. **Modern Web Browser Clients** (HTML5, CSS3, Vanilla JavaScript via HTTP static file serving and RFC 6455 WebSocket framing).
2. **Native Python Clients** (Desktop Graphical User Interface using Tkinter and a Terminal Command-Line Interface).

All connected nodes can register custom usernames, observe real-time join/leave presence notifications, view an active online user directory, and transmit real-time text messages with formatted timestamps. The entire implementation relies exclusively on the Python standard library with zero external runtime dependencies, providing high pedagogical transparency for computer networks laboratory evaluations.

---

## 1. Introduction & Objectives

### 1.1 Background & Motivation
In standard computer science curricula, students often study networking protocols theoretically—memorizing the OSI 7-layer model, TCP three-way handshakes, and IP addressing schemes. However, practical comprehension requires constructing network software that operates directly on operating system transport layer abstractions: **Network Sockets**. 

The goal of this project is to build an interactive, multi-client application operating over an IEEE 802.11 (Wi-Fi) or IEEE 802.3 (Ethernet) Local Area Network, demonstrating how raw bytes traverse physical and transport boundaries.

### 1.2 Core Project Objectives
1. **Develop a Multithreaded TCP Socket Server**: Create a centralized listener that binds to the host's private IPv4 address on TCP port 5000, accepting multiple simultaneous client connections without hanging.
2. **Implement Real-Time Broadcast Messaging**: When any user dispatches a message, the server must deserialize the payload, inject server-side verification and timestamps, and broadcast it concurrently to all active sockets.
3. **Presence & State Management**: Maintain thread-safe tracking of connected sockets, dynamically broadcasting join and leave event alerts along with updated active user lists.
4. **Build an Attractive & Modern Interface**: Deliver a responsive messaging dashboard featuring message bubbles, avatar initials, connection health monitors, and sound chimes.
5. **Demonstrate LAN Operability**: Ensure seamless communication between physical machines (laptops, desktops, smartphones) connected to the same wireless access point.
6. **Ensure Zero Third-Party Footprint**: Avoid external frameworks (e.g., Flask, Django, Node.js, socket.io) so that all socket mechanics remain transparent for laboratory viva examinations.

---

## 2. Networking Concepts Demonstrated

The application provides concrete, runnable demonstrations of the following seven core networking concepts:

### 2.1 Local Area Network (LAN)
A Local Area Network is a computer network that interconnects computers within a limited geographical area such as a computer laboratory, home, or office building. 
- In this project, devices reside in a private Class C subnet (e.g., `192.168.x.x / 24`).
- Packets are switched locally across the Wi-Fi access point / router without routing to the external Internet or cloud intermediaries.
- Host resolution occurs via local IPv4 addresses assigned by DHCP (Dynamic Host Configuration Protocol).

### 2.2 Client-Server Architecture
The system follows a classical centralized client-server model:
- **Server (`server.py`)**: A daemon process that maintains a permanent passive listening state (`LISTEN`), stores state (active client sockets and usernames), serializes traffic, and arbitrates message distribution.
- **Clients (`Web Browser`, `client_gui.py`, `client.py`)**: Active initiators that issue connection requests to the known IP and port of the server. Clients do not need to know the IP addresses of other clients; the server acts as an authoritative message broker.

### 2.3 TCP/IP Protocol Suite
The application operates at Layer 4 (Transport Layer) using **TCP (Transmission Control Protocol)** via `socket.SOCK_STREAM`:
- **Connection-Oriented**: A full duplex point-to-point connection is established via the TCP 3-Way Handshake (`SYN` -> `SYN-ACK` -> `ACK`) before any message payload is transferred.
- **Reliable Delivery**: TCP guarantees packet delivery using sequence numbers, positive acknowledgments (`ACK`), and automatic retransmission of lost segments.
- **Ordered Byte Stream**: Messages arrive in the exact order they were transmitted, eliminating packet reordering anomalies common in UDP.
- **Flow and Congestion Control**: Prevents receiver buffer overflow through sliding window flow control.

### 2.4 IP Addresses and Port Numbers
- **IP Address (Network Layer)**: Directs packets to the target network interface card (NIC). The server binds to `0.0.0.0` (wildcard address `INADDR_ANY`), enabling it to capture incoming traffic from `127.0.0.1` (loopback) and `192.168.x.x` (Wi-Fi adapter).
- **Port Number (Transport Layer)**: Identifies the specific receiving application process on the host. Defaulted to **TCP Port 5000** (an unassigned user port above the privileged `1–1023` well-known port range).

### 2.5 Socket Programming Mechanics
Sockets serve as the operating system's abstraction for endpoint network communication (Berkeley Sockets API). The sequence implemented in `server.py` follows the textbook state diagram:

$$\text{socket()} \longrightarrow \text{bind()} \longrightarrow \text{listen()} \longrightarrow \text{accept()} \longrightarrow \text{recv()} / \text{sendall()} \longrightarrow \text{close()}$$

| Socket API Primitive | Role in NetVibe |
| :--- | :--- |
| `socket(AF_INET, SOCK_STREAM)` | Creates an IPv4 TCP stream socket. |
| `setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)` | Prevents `OSError: [Errno 98] Address already in use` upon server restart. |
| `bind(('0.0.0.0', 5000))` | Associates the socket with all network interfaces on port 5000. |
| `listen(20)` | Puts socket into passive mode with a backlog queue of up to 20 connection requests. |
| `accept()` | Blocks until a client initiates a TCP handshake; returns `(conn_socket, (client_ip, client_port))`. |
| `recv(4096)` | Reads incoming data from the socket's internal OS receive buffer. |
| `sendall(bytes)` | Continuously transmits bytes until the entire buffer is sent or an error occurs. |
| `close()` | Initiates TCP graceful four-way teardown (`FIN` -> `ACK` -> `FIN` -> `ACK`). |

### 2.6 Multithreading and Concurrency
A standard single-threaded socket server halts when executing blocking operations such as `accept()` or `recv()`. If Client A is connected and idle, Client B would be blocked from connecting or receiving messages.
- NetVibe resolves this by spawning an independent `threading.Thread` for every accepted socket.
- **Mutex Lock (`threading.Lock()`)**: Access to shared data structures (the active clients registry `{socket: metadata}`) is synchronized to prevent race conditions during concurrent client connections, disconnections, and broadcasts.

### 2.7 Data Serialization and Protocol Framing
Raw TCP sockets provide a continuous stream of unformatted bytes with no inherent concept of "message boundaries" (known as the TCP packet concatenation / fragmentation issue). NetVibe demonstrates two framing methods:
1. **Newline-Delimited JSON (NDJSON)** for Native TCP clients: Messages are delimited by the `\n` character and parsed using `json.loads()`.
2. **RFC 6455 WebSocket Framing** for Web clients: Binary frames prefixed with opcode, payload length indicators, and client-to-server masking keys.

---

## 3. System Architecture & Methodology

### 3.1 Network Topology & Architecture
The diagram below illustrates the complete structural topology of the LAN deployment:

```
+-----------------------------------------------------------------------------------+
|                           LOCAL AREA NETWORK (WLAN / Wi-Fi)                       |
|                                Subnet: 192.168.1.0/24                             |
+-----------------------------------------------------------------------------------+
                                          |
                         +----------------+----------------+
                         |                                 |
                         v                                 v
        +----------------------------------+    +----------------------------------+
        |          SERVER HOST             |    |          CLIENT NODE             |
        |       IPv4: 192.168.1.15         |    |       IPv4: 192.168.1.28         |
        |                                  |    |                                  |
        |  +----------------------------+  |    |  +----------------------------+  |
        |  |     LANChatServer (TCP)    |  |    |  |  Web Browser / Tkinter GUI |  |
        |  |  Socket: 0.0.0.0:5000      |  |    |  |  Connects to:              |  |
        |  |                            |  |    |  |  192.168.1.15:5000         |  |
        |  |  [Thread Pool / Workers]   |  |    |  |                            |  |
        |  |  - Thread 1: Client Alpha  |<======|==|== TCP Stream (Port 5000)   |  |
        |  |  - Thread 2: Client Beta   |  |    |  +----------------------------+  |
        |  |  - Thread 3: Client Gamma  |  |    +----------------------------------+
        |  +----------------------------+  |
        +----------------------------------+
```

### 3.2 Protocol Lifecycle Flowchart

```mermaid
flowchart TD
    Start([Server Bootstrapped]) --> DetectIP[Detect Local IPv4 via UDP Socket]
    DetectIP --> BindSocket[Create TCP Socket & Bind to 0.0.0.0:5000]
    BindSocket --> ListenState[listen for incoming TCP connections]
    
    ListenState --> AcceptClient[accept client connection]
    AcceptClient --> SpawnThread[Spawn Dedicated Worker Thread]
    
    SpawnThread --> InspectHeader{Inspect First Bytes}
    
    InspectHeader -- Starts with 'GET /' -->> CheckWS{WebSocket Upgrade?}
    CheckWS -- Yes -->> WSHandshake[Compute SHA1 + Base64 Sec-WebSocket-Key]
    WSHandshake --> Send101[Send HTTP 101 Switching Protocols]
    Send101 --> WSLoop[Enter WebSocket Frame Receive Loop]
    
    CheckWS -- No -->> ServeHTTP[Serve index.html / style.css / script.js via HTTP 200]
    ServeHTTP --> CloseHTTP[Close HTTP Socket]
    
    InspectHeader -- Raw TCP JSON -->> TCPLoop[Enter Newline JSON Receive Loop]
    
    WSLoop --> Dispatcher[Message Dispatcher]
    TCPLoop --> Dispatcher
    
    Dispatcher --> JoinEvent{Payload Type?}
    JoinEvent -- 'join' -->> RegUser[Register Username & Broadcast Join Event]
    JoinEvent -- 'message' -->> BcastMsg[Attach Timestamp & Broadcast Message]
    JoinEvent -- 'leave' or EOF -->> Disconnect[Remove from Registry & Broadcast Leave Event]
```

---

## 4. Implementation Details

The project is structured into modular components:

### 4.1 Server Implementation (`server.py`)
- **Local IP Discovery**: Uses a dummy UDP socket to query default interface routing:
  ```python
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(('8.8.8.8', 80))
  local_ip = s.getsockname()[0]
  ```
- **Socket Initialization**:
  ```python
  self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  self.server_socket.bind(('0.0.0.0', 5000))
  self.server_socket.listen(20)
  ```
- **Unified Protocol Negotiation**: Evaluates the initial byte signature to route between HTTP static assets, WebSocket upgrades, or raw TCP sockets.
- **WebSocket Handshake Calculation**:
  ```python
  accept_raw = sec_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
  accept_sha1 = hashlib.sha1(accept_raw.encode('utf-8')).digest()
  accept_base64 = base64.b64encode(accept_sha1).decode('utf-8')
  ```
- **Thread Synchronization**: Locks `self.clients_lock` before altering the connected clients dictionary during join, broadcast, and leave actions.

### 4.2 Web Interface (`static/index.html`, `style.css`, `script.js`)
- **Login Modal**: Captures user identity, server IPv4, and port.
- **Chat Dashboard**: Modern glassmorphic sidebar featuring real-time online user count, user pills with unique avatar background colors derived via string hashing, and active connection badges.
- **Message Rendering**: Differentiates between sent bubbles (right-aligned gradient) and received bubbles (left-aligned dark card with author tags and timestamps).
- **Audio Feedback**: Uses the browser's native **Web Audio API** (`OscillatorNode` and `GainNode`) to synthesize dynamic acoustic notification frequencies upon receiving messages, requiring zero external audio assets.

### 4.3 Native Desktop Client (`client_gui.py`)
- Developed using Python's native `tkinter` and `tkinter.scrolledtext`.
- Spawns a background daemon thread running `client_socket.recv()` to avoid freezing the GUI main event loop (`root.mainloop()`).
- Safely queues received packets to the main UI thread using `root.after()`.

### 4.4 Automated Test Suite (`test_lan_chat.py`)
- Instantiates a mock server on port 5002.
- Connects three virtual clients (Alice via Raw TCP, Bob via Raw TCP, and Charlie via RFC 6455 WebSocket).
- Verifies message transmission, cross-protocol delivery, join/leave broadcasts, and clean disconnections.

---

## 5. Experimental Results & Verification

### 5.1 Test Cases and Results Matrix

| Test ID | Test Scenario | Expected Outcome | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **TC-01** | Server Startup & Port Binding | Socket binds to `0.0.0.0:5000`, discovers local IPv4, and enters `LISTEN` state. | Server successfully binds to port 5000; detects IPv4 `192.168.212.55`. | **PASS** |
| **TC-02** | HTTP Asset Delivery | Web browser requests `/`, `/static/style.css`, `/static/script.js`. | Server returns HTTP 200 with appropriate MIME types. | **PASS** |
| **TC-03** | RFC 6455 WebSocket Handshake | Web client sends `Upgrade: websocket`; server computes SHA1/Base64 key. | HTTP 101 Switching Protocols returned; WebSocket connection established. | **PASS** |
| **TC-04** | Multi-Client Connection | Multiple clients (Alice, Bob, Charlie) connect simultaneously. | Server spawns dedicated threads; registers each client in thread-safe map. | **PASS** |
| **TC-05** | Real-Time Message Broadcast | Bob transmits `"Hello NetVibe!"`. | Message is received instantaneously by Alice and Charlie with timestamp and sender tags. | **PASS** |
| **TC-06** | Cross-Protocol Interoperability | WebSocket client (Charlie) transmits message to Raw TCP client (Alice). | Message correctly encapsulated and delivered to both endpoints. | **PASS** |
| **TC-07** | Disconnection & State Cleanup | Bob disconnects. | Socket closed; server decrements online count and broadcasts `"🚪 Bob left the chat."`. | **PASS** |
| **TC-08** | Automated Test Suite Run | Execute `python test_lan_chat.py`. | All 6 test suites execute and pass in < 2.0s with 0 errors. | **PASS** |

### 5.2 Automated Test Execution Output
Execution of `python test_lan_chat.py` yielded:

```
=================================================================
      🧪 NetVibe LAN Chat Application - Automated Test Suite 🧪
=================================================================

[1] Starting LANChatServer on port 5002...
[*] Server Status        : ONLINE
[*] Transport Protocol   : TCP / IP (SOCK_STREAM)
[*] Bound Host           : 127.0.0.1 (All Interfaces)
[*] Local IPv4 Address   : 192.168.212.55
[*] TCP Port             : 5002

    ✓ Server is up and listening on TCP socket.

[2] Connecting Client 1: Alice (Raw TCP Socket)...
[+] [CONNECT] Client socket connected: 127.0.0.1:61964 (Raw TCP)
[+] [JOIN] User 'Alice' joined the chat. Online count: 1
    ✓ Alice connected & received 'welcome' packet.
    ✓ Online count on server: 1

[3] Connecting Client 2: Bob (Raw TCP Socket)...
[+] [CONNECT] Client socket connected: 127.0.0.1:61965 (Raw TCP)
[+] [JOIN] User 'Bob' joined the chat. Online count: 2
    ✓ Bob connected. Server registered 2 online users.
    ✓ Alice successfully received Bob's join notification.

[4] Connecting Client 3: Charlie (WebSocket / Web Client)...
[+] [CONNECT] Client socket connected: 127.0.0.1:61966 (WebSocket)
[+] [JOIN] User 'Charlie' joined the chat. Online count: 3
    ✓ Charlie completed RFC 6455 handshake & joined.
    ✓ Server successfully bridged Raw TCP and WebSocket clients!

[5] Testing Real-Time Messaging: Bob sends 'Hello NetVibe!'...
[MSG] [04:52 PM] <Bob>: Hello NetVibe!
    ✓ Alice (Raw TCP) received Bob's message with correct timestamp & sender.
    ✓ Charlie (WebSocket) received Bob's message across protocol boundary.

[6] Testing Web Messaging: Charlie sends 'Greetings from Web!'...
[MSG] [04:52 PM] <Charlie>: Greetings from Web!
    ✓ Both TCP clients received WebSocket client's message.

[7] Testing Disconnection Handling: Bob disconnects...
[-] [LEAVE] User 'Bob' disconnected. Online count: 2
    ✓ Alice received leave notification: '🚪 Bob left the chat.'
    ✓ Online count properly decremented to: 2

=================================================================
     🎉 ALL 6 TEST SUITES PASSED FLAWLESSLY! (100% SUCCESS) 🎉
=================================================================
```

---

## 6. Practical Demonstration & Screenshot Capture Guide

For laboratory evaluation and project report submission, capture the following screenshots:

### Screenshot 1: Server Initialization
- **Action**: Open terminal, navigate to project folder, and run:
  ```bash
  python server.py
  ```
- **Capture**: The terminal displaying the ASCII banner, detected Local IPv4 address (e.g. `192.168.x.x`), and active TCP Port `5000`.

### Screenshot 2: Web Login Screen
- **Action**: Open browser at `http://localhost:5000` (or `http://<SERVER_IP>:5000` from another laptop/phone).
- **Capture**: The login card showing the username input, server IP field, and networking concept badges.

### Screenshot 3: Active Multi-User Chat Session
- **Action**: Open two side-by-side browser windows (or one laptop and one mobile browser). Log in as **"Alice"** in Window 1 and **"Bob"** in Window 2. Exchange several messages.
- **Capture**: Both windows side-by-side displaying:
  1. Sent and received message bubbles with distinct styling.
  2. The online users panel showing both active usernames.
  3. Formatted timestamps on messages.
  4. System notification banners showing user join events.

### Screenshot 4: Native Python Desktop GUI Client
- **Action**: Run `python client_gui.py` in a terminal and join as **"Charlie"**.
- **Capture**: The Tkinter GUI window showing the active user list in the sidebar and real-time message history synchronized with the web clients.

### Screenshot 5: User Disconnection & Server Logs
- **Action**: Close one of the client windows or click "Disconnect".
- **Capture**: The remaining client's screen showing the `"🚪 User left the chat"` banner, and the server terminal showing the disconnect log and decremented online count.

### Screenshot 6: Automated Test Suite Output
- **Action**: Run `python test_lan_chat.py`.
- **Capture**: The terminal output showing all 6 test suites passing with 100% success.

---

## 7. Conclusion & Future Enhancements

### 7.1 Conclusion
The **NetVibe** LAN Chat Application successfully fulfills all requirements established for Continuous Assessment 4. By developing a clean, multithreaded TCP socket server and implementing client-side endpoints across web browsers and native desktop applications, the project demonstrates how fundamental transport layer primitives can power modern, real-time interactive systems. 

Key technical takeaways:
- **TCP reliability** eliminates the need for application-layer packet loss recovery.
- **Multithreading** is essential for preventing I/O starvation in synchronous network software.
- Operating on standard library primitives provides complete algorithmic transparency, ideal for computer networks laboratory evaluations.

### 7.2 Future Enhancements
1. **End-to-End Encryption (E2EE)**: Incorporating AES-256 or RSA asymmetric key exchange over the TCP socket to secure message content against local LAN packet sniffing (e.g., Wireshark).
2. **Binary File & Image Sharing**: Adding chunked binary streaming over TCP sockets to enable peer-to-peer file transfer.
3. **Private Direct Messaging**: Supporting a `/msg <username> <text>` syntax for targeted point-to-point communication in addition to group broadcasts.
4. **Persistent Message History**: Integrating an embedded SQLite database to archive chat logs across server restarts.

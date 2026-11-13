# Computer Networks Lab Viva Examination Guide
## 35+ Viva Questions and Comprehensive Answers: NetVibe LAN Chat Project

This reference document prepares students for the oral viva examination and laboratory practical evaluation for **Continuous Assessment 4 (CA-4)**.

---

### Section 1: Socket Programming & System Calls

#### Q1: What is a socket in computer networks?
**Answer:** A socket is an abstract software endpoint created by the operating system that enables bidirectional communication between two processes across a computer network. In the Berkeley Sockets API, a socket is identified by a combination of an **IP address**, a **port number**, and a **transport layer protocol** (e.g., TCP or UDP).

#### Q2: What is the significance of `socket.AF_INET` and `socket.SOCK_STREAM`?
**Answer:**
- `AF_INET` specifies the address family: **IPv4** (32-bit internet protocol addresses).
- `SOCK_STREAM` specifies the socket type: **TCP (Transmission Control Protocol)**, which provides a sequenced, reliable, two-way, connection-oriented byte stream. (In contrast, `SOCK_DGRAM` corresponds to UDP).

#### Q3: Explain the sequence of socket system calls on the server side in TCP.
**Answer:**
1. `socket()`: Creates a new endpoint for communication.
2. `bind()`: Assigns a local IP address and port number to the socket.
3. `listen()`: Puts the socket into passive mode to wait for client connection requests.
4. `accept()`: Blocks until a client connection arrives, completing the TCP 3-way handshake and returning a *new* socket descriptor dedicated to that client.
5. `recv()` / `sendall()`: Reads and writes data over the established connection.
6. `close()`: Closes the connection and releases socket resources.

#### Q4: Why does `accept()` return a new socket rather than using the listening socket?
**Answer:** The listening socket (`server_socket`) is dedicated solely to listening on port 5000 and accepting incoming connection requests. If it were used for data transmission, the server would be unable to accept connections from other clients while communicating with the first client. Therefore, `accept()` returns a *newly created connected socket* specifically for data transfer with that particular client, leaving the original socket free to accept new incoming connections.

#### Q5: What is the purpose of `setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`?
**Answer:** When a TCP server shuts down, the port often enters the `TIME_WAIT` state for 1 to 2 minutes to ensure lingering packets in the network are cleared. Setting `SO_REUSEADDR` tells the operating system kernel to allow the immediate reuse of the local socket address and port upon server restart, preventing the common `OSError: [Errno 98/10048] Address already in use` error.

#### Q6: What is the backlog parameter in `socket.listen(backlog)`?
**Answer:** The backlog parameter specifies the maximum number of pending, unaccepted connections the operating system can hold in its queue before rejecting new connection attempts. In NetVibe, `server_socket.listen(20)` allows up to 20 connection requests to wait in the OS backlog queue while the server is busy spawning threads.

#### Q7: What is the difference between `send()` and `sendall()` in Python socket programming?
**Answer:**
- `send()` transmits data but may send only a portion of the buffer if the network buffer is full, returning the number of bytes actually sent. The programmer must manually loop until all bytes are sent.
- `sendall()` is a high-level wrapper that repeatedly calls `send()` under the hood until the entire byte buffer has been transmitted or an error occurs. NetVibe uses `sendall()` to guarantee complete packet transmission.

#### Q8: How does the server know when a client has disconnected?
**Answer:** In TCP, when a client closes its socket gracefully, the client OS sends a `FIN` packet. On the server side, calling `socket.recv(BUFFER_SIZE)` returns an empty byte string (`b""`). If `not data` evaluates to True, the server recognizes that the connection has been terminated by the client and initiates its cleanup procedure.

---

### Section 2: Transport Layer & TCP/IP Protocol

#### Q9: Why did you choose TCP over UDP for this chat application?
**Answer:** TCP is chosen because text chat requires **guaranteed reliability, zero packet loss, and strict in-order delivery**. 
- If UDP were used, chat messages or system notifications could be dropped, duplicated, or received out of order without any notification.
- TCP handles sequence numbering, acknowledgments (`ACK`), checksum verification, and automatic retransmissions transparently at the transport layer.

#### Q10: How does the TCP Three-Way Handshake work in NetVibe?
**Answer:** When a client calls `socket.connect((host, port))`:
1. **SYN**: Client sends a `SYN` (Synchronize) segment with an initial sequence number ($ISN_c$) to the server.
2. **SYN-ACK**: The server receives the `SYN`, allocates resources, and responds with a `SYN-ACK` segment containing its own sequence number ($ISN_s$) and an acknowledgment number ($ACK = ISN_c + 1$).
3. **ACK**: The client sends an `ACK` ($ACK = ISN_s + 1$). The connection transitions to the `ESTABLISHED` state on both endpoints, and `accept()` unblocks on the server.

#### Q11: How does TCP connection termination (Four-Way Handshake) work?
**Answer:**
1. **FIN from Client**: Client initiates disconnect by sending `FIN`.
2. **ACK from Server**: Server acknowledges the `FIN` with an `ACK` (Client-to-Server half-close).
3. **FIN from Server**: Server completes sending any pending data and transmits its own `FIN`.
4. **ACK from Client**: Client acknowledges the server's `FIN` with an `ACK`. The connection is completely closed.

#### Q12: What is the "TCP Streaming Problem" (packet fragmentation/concatenation), and how did you solve it?
**Answer:** TCP is a continuous byte stream protocol, not a message-based protocol. It does not preserve application-layer message boundaries. Two separate messages sent sequentially could arrive together in one `recv()` call (concatenation) or a single large message could be split across multiple `recv()` calls (fragmentation).
- NetVibe solves this for raw TCP clients by using **delimiter framing**: every JSON message ends with a newline character (`\n`). The client and server buffer incoming data and split by `\n` to reconstruct intact application messages.
- For web clients, the application uses **WebSocket framing**, which explicitly encodes payload length in the frame header.

---

### Section 3: Multithreading & Concurrency

#### Q13: Why is multithreading necessary in a chat server?
**Answer:** In a single-threaded server, socket calls like `accept()` and `recv()` are blocking. If the server is waiting for Client A to type a message inside `recv()`, it cannot accept incoming connections from Client B, nor can it deliver messages sent by other users. Multithreading allows the server to handle each client on an independent execution thread concurrently.

#### Q14: How does NetVibe implement multithreading?
**Answer:** For every accepted connection from `server_socket.accept()`, the main loop spawns a worker thread:
```python
client_thread = threading.Thread(
    target=self.handle_client,
    args=(client_socket, client_address),
    daemon=True
)
client_thread.start()
```
The worker thread executes `handle_client()` to listen for messages from that client, while the main thread immediately loops back to `accept()` the next client.

#### Q15: What is a Race Condition, and how did you prevent it?
**Answer:** A race condition occurs when multiple threads attempt to read and write shared data concurrently without synchronization, leading to data corruption. In NetVibe, the dictionary `self.clients` is shared across all worker threads. To prevent race conditions during simultaneous user joins, disconnects, or broadcasts, access to the dictionary is wrapped in a **Mutual Exclusion Lock (`threading.Lock()`)**:
```python
with self.clients_lock:
    self.clients[client_socket] = client_info
```

#### Q16: What is a daemon thread (`daemon=True`)?
**Answer:** A daemon thread runs in the background and is terminated automatically when the main program thread exits. By marking client threads as daemon threads, the entire server process can shut down immediately upon receiving a `KeyboardInterrupt` (`Ctrl+C`) without hanging on background loops.

---

### Section 4: Network Addressing & LAN Configuration

#### Q17: What does binding to IP address `0.0.0.0` mean?
**Answer:** `0.0.0.0` represents `INADDR_ANY` (all IPv4 addresses on the local machine). It instructs the operating system to bind the socket to every available network adapter—including `127.0.0.1` (loopback) and `192.168.x.x` (Wi-Fi/Ethernet interface). If the server were bound only to `127.0.0.1`, it could only accept connections from the same physical machine.

#### Q18: How does the server automatically detect its local IPv4 address?
**Answer:** By opening a dummy UDP socket and attempting a connection to an external address:
```python
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
```
Because UDP is connectionless, no packets are actually transmitted across the wire. However, the OS routing table determines which local network interface would be used to reach `8.8.8.8`, returning the active LAN IPv4 address (e.g., `192.168.1.15`).

#### Q19: Why do we use port 5000 by default? Can any port number be used?
**Answer:** Port numbers range from $0$ to $65535$:
- **0 – 1023**: Well-Known / System Ports (reserved for HTTP 80, HTTPS 443, SSH 22; require administrative/root privileges).
- **1024 – 49151**: Registered / User Ports.
- **49152 – 65535**: Dynamic / Ephemeral Ports.  
Port 5000 is a standard unprivileged user port, avoiding conflicts with operating system services while requiring no special system privileges.

#### Q20: What is the difference between a Private IP and a Public IP?
**Answer:**
- **Private IP (RFC 1918)**: Used exclusively within Local Area Networks (e.g., `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`). They are not routable across the global public internet and must use NAT (Network Address Translation) to reach external hosts. NetVibe operates on private IP addresses.
- **Public IP**: Globally unique IP addresses assigned by IANA/ISPs, routable across the global Internet.

#### Q21: What is the subnet mask, and what does `192.168.1.0/24` signify?
**Answer:** The subnet mask separates the IP address into the **Network ID** and **Host ID**. In `/24` CIDR notation (subnet mask `255.255.255.0`), the first 24 bits represent the network prefix, leaving $32 - 24 = 8$ bits for host addresses ($2^8 - 2 = 254$ usable client devices on the LAN).

---

### Section 5: WebSockets, HTTP & Web Technologies

#### Q22: What is the difference between HTTP and WebSocket?
**Answer:**
- **HTTP**: A stateless, request-response, half-duplex application protocol. The client must initiate a request, and the server returns a response and closes or idles the connection. The server cannot push unrequested data to the client.
- **WebSocket (RFC 6455)**: A stateful, full-duplex, persistent communication channel running over a single TCP connection. Once the handshake is completed, either client or server can transmit data frames at any time with minimal overhead (as little as 2 bytes of header per frame).

#### Q23: How does the WebSocket Handshake transition from HTTP?
**Answer:**
1. The browser initiates a standard HTTP GET request with upgrade headers:
   ```http
   GET /ws HTTP/1.1
   Host: 192.168.1.15:5000
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13
   ```
2. The server reads the key, concatenates it with the magic GUID `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`, hashes it with SHA-1, encodes the digest in Base64, and responds with:
   ```http
   HTTP/1.1 101 Switching Protocols
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
   ```
3. From that moment on, the TCP socket switches from HTTP parsing to binary WebSocket frame parsing.

#### Q24: Why are client-to-server WebSocket frames masked?
**Answer:** RFC 6455 requires all frames sent from client to server to be masked using a 4-byte random masking key. This security measure prevents malicious scripts from confusing caching proxy servers into executing cache poisoning attacks. Server-to-client frames are unmasked.

---

### Section 6: Architecture, Security & Error Handling

#### Q25: How does the server perform broadcast messaging?
**Answer:** When the server receives a message from Client A:
1. It parses the JSON packet and verifies the sender's identity.
2. It generates a standardized broadcast payload with the sender's username, message text, and server timestamp.
3. It iterates over all active sockets stored in `self.clients` and dispatches the payload to each connected socket using `sendall()`.

#### Q26: How does the server differentiate between Web clients and Raw TCP clients?
**Answer:** Upon accepting a new socket connection, the server inspects the first chunk of incoming bytes. 
- If the bytes start with `GET ` or `POST `, the connection is recognized as an HTTP request (served as static web files or upgraded to WebSocket).
- If the bytes do not begin with an HTTP method (e.g. JSON starting with `{`), the server routes the socket to the native raw TCP packet handler.

#### Q27: How does Tkinter handle incoming socket messages without freezing the GUI?
**Answer:** Tkinter is single-threaded; its event loop runs in `root.mainloop()`. If a blocking `socket.recv()` call were placed in the main thread, the entire GUI would freeze and become unresponsive. NetVibe resolves this by running `recv()` in a background worker thread. When a packet arrives, it schedules the UI update in the main thread using `root.after(0, callback, data)`, preserving thread safety.

#### Q28: How does the Web interface prevent Cross-Site Scripting (XSS)?
**Answer:** If a user sends a chat message containing malicious HTML or JavaScript (e.g. `<script>alert('hacked')</script>`), directly inserting it via `.innerHTML` could execute arbitrary code in other users' browsers. NetVibe prevents this with an `escapeHtml()` sanitization function that converts `<`, `>`, `&`, `"`, and `'` into safe HTML character entities before appending to the DOM.

#### Q29: What causes "Connection Refused" (WinError 10061)?
**Answer:** `Connection Refused` indicates that the client's TCP `SYN` packet reached the destination host, but the operating system kernel rejected it with a `RST` (Reset) packet because no active process was listening on the requested port (port 5000), or the firewall actively blocked the port.

#### Q30: What happens if two users pick the exact same username?
**Answer:** In the current implementation, users are identified by their unique socket file descriptor. If two users enter "Alice", both can chat, but to avoid visual ambiguity, the server can be configured to enforce unique usernames by appending a numeric identifier or checking `self.get_active_usernames()` before acknowledging the `join` packet.

---

### Section 7: Advanced & Conceptual Viva Questions

#### Q31: Map NetVibe's components to the 7 Layers of the OSI Model.
**Answer:**
- **Layer 7 (Application)**: NetVibe JSON message schema, HTTP 1.1, WebSocket protocol.
- **Layer 6 (Presentation)**: UTF-8 encoding, JSON serialization/deserialization, Base64/SHA-1 hashing.
- **Layer 5 (Session)**: User session management, client registry, presence tracking (join/leave states).
- **Layer 4 (Transport)**: TCP (`SOCK_STREAM`), port numbers (port 5000), flow/congestion control, 3-way handshake.
- **Layer 3 (Network)**: IPv4 addressing, local routing between LAN interfaces (`192.168.x.x`).
- **Layer 2 (Data Link)**: Ethernet frames, Wi-Fi 802.11 frames, MAC address resolution via ARP.
- **Layer 1 (Physical)**: Radio frequency waves (Wi-Fi) or copper twisted-pair cables (RJ-45 Ethernet).

#### Q32: What is the role of ARP (Address Resolution Protocol) when Client A communicates with the Server?
**Answer:** Before Client A's NIC can transmit an IP packet to the server's IP address (`192.168.1.15`), it must determine the server's physical 48-bit **MAC address**. Client A broadcasts an **ARP Request** (`"Who has 192.168.1.15? Tell 192.168.1.22"`). The server responds with a unicast **ARP Reply** containing its MAC address. Client A caches this entry in its ARP table and encapsulates the TCP/IP packet inside an Ethernet/Wi-Fi frame.

#### Q33: What is "Wi-Fi AP Isolation" (Client Isolation), and why might it block LAN chat in college labs?
**Answer:** AP Isolation is a security feature on enterprise routers that blocks wireless clients connected to the same Wi-Fi network from communicating directly with one another. If enabled on a university campus Wi-Fi network, clients cannot connect to `http://<SERVER_IP>:5000`. The workaround is connecting all devices to a personal **Mobile Hotspot**, where client isolation is disabled by default.

#### Q34: What is the difference between synchronous I/O, multithreading, and asynchronous I/O (`asyncio`)?
**Answer:**
- **Synchronous I/O**: Operations block the thread until complete; handles one client at a time.
- **Multithreading** (Used in NetVibe): OS manages multiple concurrent threads; each blocking socket gets its own thread. Simple to conceptualize and explain in undergraduate coursework.
- **Asynchronous I/O (`asyncio` / `select` / `epoll`)**: Single-threaded event loop that handles thousands of concurrent non-blocking sockets using I/O multiplexing primitives.

#### Q35: How would you secure this LAN Chat application in a production environment?
**Answer:**
1. **Transport Layer Security (TLS/SSL)**: Wrap the TCP socket using Python's `ssl.wrap_socket()`, upgrading HTTP to HTTPS and WebSocket to WSS (`wss://`), encrypting all LAN traffic against Wireshark packet sniffing.
2. **User Authentication**: Implement password hashing using `bcrypt` or salted SHA-256 with JWT tokens.
3. **Rate Limiting**: Restrict the number of messages a client can send per second to mitigate Denial of Service (DoS) flood attacks.

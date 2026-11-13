/**
 * NetVibe - Client-Side Real-Time WebSocket Logic
 * Computer Networks Lab CA-4 Mini-Project
 */

// Application State
let ws = null;
let currentUsername = "";
let serverHost = "";
let serverPort = 5000;
let isConnected = false;

// Audio Context for synthetic sound effects (zero external files required)
let audioCtx = null;

function initAudio() {
  try {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContext();
    }
  } catch (e) {
    console.warn("Web Audio API not supported", e);
  }
}

function playNotificationSound(type = 'msg') {
  try {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;
    if (type === 'msg') {
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.1); // A5
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
    } else if (type === 'join') {
      osc.frequency.setValueAtTime(440, now); // A4
      osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.15); // E5
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    }
  } catch (err) {
    // Audio autoplay policy might restrict before user interaction
  }
}

// Color Palette generator for unique user avatars
const AVATAR_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#10b981', 
  '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', 
  '#ec4899', '#14b8a6', '#84cc16'
];

function getAvatarColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
}

// Initialize IP inputs on page load
window.addEventListener('DOMContentLoaded', () => {
  const detectedHost = window.location.hostname || "127.0.0.1";
  const detectedPort = window.location.port || "5000";

  const hostInput = document.getElementById('server-ip-input');
  const portInput = document.getElementById('server-port-input');

  if (hostInput) hostInput.value = detectedHost;
  if (portInput) portInput.value = detectedPort;

  // Pre-fill random friendly username placeholder
  const sampleUsers = ["CyberSurfer", "ByteCoder", "PacketPilot", "RouterRanger", "SocketNinja"];
  const randomName = sampleUsers[Math.floor(Math.random() * sampleUsers.length)];
  const userInput = document.getElementById('username-input');
  if (userInput && !userInput.value) {
    userInput.placeholder = `e.g. ${randomName}`;
  }
});

// ========================================================
// 1. JOIN & CONNECTION LOGIC
// ========================================================
function joinChat() {
  initAudio();
  const usernameInput = document.getElementById('username-input');
  const ipInput = document.getElementById('server-ip-input');
  const portInput = document.getElementById('server-port-input');
  const errorBanner = document.getElementById('login-error');
  const joinBtn = document.getElementById('join-btn');

  const username = usernameInput.value.trim();
  const host = ipInput.value.trim() || window.location.hostname || '127.0.0.1';
  const port = portInput.value.trim() || '5000';

  if (!username) {
    showLoginError("Please enter a valid username.");
    return;
  }

  currentUsername = username;
  serverHost = host;
  serverPort = port;

  // Disable button and show connecting state
  joinBtn.disabled = true;
  joinBtn.innerHTML = `<span>Connecting TCP Socket...</span>`;
  errorBanner.classList.add('hidden');

  // Determine WebSocket URL
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${host}:${port}/ws`;

  console.log(`[LAN Chat] Connecting to WebSocket: ${wsUrl}`);

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[LAN Chat] TCP Connection established & WebSocket handshake completed!");
      isConnected = true;
      // Send JOIN packet
      const joinPacket = {
        type: "join",
        username: currentUsername
      };
      ws.send(JSON.stringify(joinPacket));
    };

    ws.onmessage = (event) => {
      handleIncomingPacket(event.data);
    };

    ws.onerror = (err) => {
      console.error("[LAN Chat] WebSocket error:", err);
      showLoginError(`Failed to connect to ${host}:${port}. Verify server.py is running and Wi-Fi firewall allows port 5000.`);
      resetJoinButton();
      updateConnectionStatus(false);
    };

    ws.onclose = () => {
      console.warn("[LAN Chat] WebSocket connection closed.");
      isConnected = false;
      updateConnectionStatus(false);
      appendSystemNotification("⚠️ Disconnected from server. Check network connection.");
    };

  } catch (err) {
    showLoginError("Socket error: " + err.message);
    resetJoinButton();
  }
}

function showLoginError(msg) {
  const errorBanner = document.getElementById('login-error');
  errorBanner.textContent = msg;
  errorBanner.classList.remove('hidden');
}

function resetJoinButton() {
  const joinBtn = document.getElementById('join-btn');
  joinBtn.disabled = false;
  joinBtn.innerHTML = `
    <span class="btn-text">Connect & Join Room</span>
    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
    </svg>
  `;
}

// ========================================================
// 2. PACKET DISPATCHER
// ========================================================
function handleIncomingPacket(rawJson) {
  let packet;
  try {
    packet = JSON.parse(rawJson);
  } catch (e) {
    console.error("Invalid packet JSON:", rawJson);
    return;
  }

  const type = packet.type;

  if (type === 'welcome') {
    // Switch from Login View to Chat View
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('chat-screen').classList.add('active');

    // Update Profile in sidebar
    document.getElementById('my-username-disp').textContent = currentUsername;
    document.getElementById('my-avatar').textContent = currentUsername.charAt(0).toUpperCase();
    document.getElementById('my-avatar').style.backgroundColor = getAvatarColor(currentUsername);

    // Update connection info in sidebar
    document.getElementById('disp-server-ip').textContent = packet.server_ip || serverHost;
    document.getElementById('disp-server-port').textContent = packet.port || serverPort;
    updateConnectionStatus(true);

    // Update active user list
    if (packet.users) {
      updateUsersList(packet.users);
    }

    appendSystemNotification(`Connected as ${currentUsername}. Welcome to LAN Chat!`);
    playNotificationSound('join');

    // Auto-focus message input
    document.getElementById('message-input').focus();

  } else if (type === 'notification') {
    appendSystemNotification(packet.message);
    if (packet.users) {
      updateUsersList(packet.users);
    }
    playNotificationSound('join');

  } else if (type === 'message') {
    appendChatMessage(packet);
    if (packet.sender !== currentUsername) {
      playNotificationSound('msg');
    }
  }
}

// ========================================================
// 3. UI RENDERING: MESSAGES & NOTIFICATIONS
// ========================================================
function appendChatMessage(data) {
  const container = document.getElementById('messages-container');
  const isMe = (data.sender === currentUsername);

  const row = document.createElement('div');
  row.className = `message-row ${isMe ? 'sent' : 'received'}`;

  const avatarColor = getAvatarColor(data.sender);
  const initial = data.sender.charAt(0).toUpperCase();

  row.innerHTML = `
    <div class="msg-avatar" style="background-color: ${avatarColor}">
      ${initial}
    </div>
    <div class="bubble-wrap">
      <div class="msg-meta">
        <span class="sender-name" style="${!isMe ? `color: ${avatarColor}` : ''}">${escapeHtml(data.sender)}</span>
        <span class="msg-time">${data.timestamp || ''}</span>
      </div>
      <div class="msg-bubble">
        ${escapeHtml(data.message)}
      </div>
    </div>
  `;

  container.appendChild(row);
  scrollToBottom();
}

function appendSystemNotification(text) {
  const container = document.getElementById('messages-container');
  const notif = document.createElement('div');
  notif.className = 'system-notification';
  notif.innerHTML = `
    <span class="notif-dot">●</span>
    <span>${escapeHtml(text)}</span>
  `;
  container.appendChild(notif);
  scrollToBottom();
}

function updateUsersList(users) {
  const listEl = document.getElementById('users-list');
  const countBadge = document.getElementById('online-count');
  listEl.innerHTML = '';

  countBadge.textContent = users.length;

  users.forEach(user => {
    const isMe = (user === currentUsername);
    const color = getAvatarColor(user);
    const initial = user.charAt(0).toUpperCase();

    const userItem = document.createElement('div');
    userItem.className = 'user-item';
    userItem.innerHTML = `
      <div class="avatar" style="background-color: ${color}">
        ${initial}
        <span class="avatar-online-dot"></span>
      </div>
      <span class="user-name">${escapeHtml(user)}</span>
      ${isMe ? '<span class="user-you-tag">YOU</span>' : ''}
    `;
    listEl.appendChild(userItem);
  });
}

function updateConnectionStatus(online) {
  const dot = document.getElementById('status-dot');
  const label = document.getElementById('status-label');
  const badge = document.getElementById('header-conn-badge');

  if (online) {
    dot.className = 'status-indicator online';
    label.textContent = 'Connected';
    label.style.color = 'var(--success)';
    badge.style.display = 'flex';
  } else {
    dot.className = 'status-indicator offline';
    label.textContent = 'Disconnected';
    label.style.color = 'var(--danger)';
    badge.style.display = 'none';
  }
}

function scrollToBottom() {
  const container = document.getElementById('messages-container');
  container.scrollTop = container.scrollHeight;
}

// ========================================================
// 4. MESSAGE TRANSMISSION & ACTIONS
// ========================================================
function sendMessage() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    alert("Socket is not connected. Please re-join the server.");
    return;
  }

  const input = document.getElementById('message-input');
  const text = input.value.trim();

  if (!text) return;

  const packet = {
    type: "message",
    message: text
  };

  ws.send(JSON.stringify(packet));
  input.value = '';
  input.focus();
}

function insertEmoji(emoji) {
  const input = document.getElementById('message-input');
  input.value += emoji;
  input.focus();
}

function leaveChat() {
  if (confirm("Are you sure you want to disconnect from NetVibe LAN Chat?")) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "leave" }));
      ws.close();
    }
    // Return to login screen
    document.getElementById('chat-screen').classList.remove('active');
    document.getElementById('login-screen').classList.add('active');
    resetJoinButton();
    document.getElementById('messages-container').innerHTML = `
      <div class="welcome-banner">
        <div class="banner-icon">💬</div>
        <h3>Welcome to NetVibe LAN Chat!</h3>
        <p>Messages exchanged here are transmitted via raw TCP packets on port 5000 across your local Wi-Fi network.</p>
      </div>
    `;
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('mobile-open');
}

// Helper: Escape HTML to prevent XSS attacks
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

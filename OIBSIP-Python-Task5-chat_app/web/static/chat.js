/*
chat.js
Handles the real-time side of the chat room page:
- connects via Socket.IO
- joins the room and renders loaded history
- sends/receives messages
- shows a desktop Notification for new messages when the tab is not
  focused (falls back silently if the browser denies/lacks support)
*/

const socket = io();
const messagesPane = document.getElementById("messages");
const form = document.getElementById("message-form");
const input = document.getElementById("message-input");

let tabFocused = true;
window.addEventListener("focus", () => { tabFocused = true; });
window.addEventListener("blur", () => { tabFocused = false; });

// Ask for notification permission once, up front. Safe to call even if
// the browser doesn't support it or the user has already answered.
if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
}

function formatTime(isoString) {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function appendMessage(username, content, timeLabel, isSelf) {
    const row = document.createElement("div");
    row.className = "message-row" + (isSelf ? " message-self" : "");

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = `[${timeLabel}] ${username}`;

    const body = document.createElement("div");
    body.className = "message-body";
    body.textContent = content;

    row.appendChild(meta);
    row.appendChild(body);
    messagesPane.appendChild(row);
    messagesPane.scrollTop = messagesPane.scrollHeight;
}

function appendSystemMessage(text, timeLabel) {
    const row = document.createElement("div");
    row.className = "message-row message-system";
    row.textContent = timeLabel ? `[${timeLabel}] ${text}` : text;
    messagesPane.appendChild(row);
    messagesPane.scrollTop = messagesPane.scrollHeight;
}

function notifyIfUnfocused(username, content) {
    if (tabFocused) return;
    if (!("Notification" in window)) return;
    if (Notification.permission !== "granted") return;
    try {
        new Notification(`${username} in #${ROOM_NAME}`, { body: content });
    } catch (e) {
        // Some browsers/environments can throw here; fail silently.
    }
}

socket.on("connect", () => {
    socket.emit("join", { room: ROOM_NAME });
});

socket.on("history", (data) => {
    messagesPane.innerHTML = "";
    (data.messages || []).forEach((m) => {
        appendMessage(m.username, m.content, formatTime(m.created_at), m.username === USERNAME);
    });
});

socket.on("new_message", (m) => {
    const isSelf = m.username === USERNAME;
    appendMessage(m.username, m.content, formatTime(m.created_at), isSelf);
    if (!isSelf) {
        notifyIfUnfocused(m.username, m.content);
    }
});

socket.on("system_message", (data) => {
    appendSystemMessage(data.text, data.time);
});

socket.on("system_error", (data) => {
    appendSystemMessage("Error: " + data.message);
});

form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    socket.emit("send_message", { room: ROOM_NAME, message: text });
    input.value = "";
});

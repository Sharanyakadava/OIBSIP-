"""
server.py
Beginner-tier chat server: raw TCP sockets + threading, no external
dependencies. Relays messages between all connected clients (run two
client.py instances against it for the classic two-user chat).

Run:
    python server.py
Then, in separate terminals:
    python client.py
    python client.py
"""

import socket
import threading
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5555

# conn -> username, guarded by a lock since each client is handled on its
# own thread.
clients = {}
clients_lock = threading.Lock()


def timestamp():
    return datetime.now().strftime("%H:%M")


def broadcast(message, exclude_conn=None):
    """Send a line to every connected client except (optionally) one."""
    dead_conns = []
    with clients_lock:
        for conn in clients:
            if conn is exclude_conn:
                continue
            try:
                conn.sendall((message + "\n").encode("utf-8"))
            except OSError:
                dead_conns.append(conn)
        for conn in dead_conns:
            clients.pop(conn, None)


def handle_client(conn, addr):
    username = None
    try:
        conn.sendall(b"Enter your username: ")
        raw = conn.recv(1024)
        if not raw:
            return
        username = raw.decode("utf-8").strip() or f"Guest-{addr[1]}"

        with clients_lock:
            clients[conn] = username

        join_msg = f"[{timestamp()}] *** {username} has joined the chat ***"
        print(join_msg)
        broadcast(join_msg, exclude_conn=conn)
        conn.sendall(f"Welcome, {username}! Type a message and press Enter. Type /quit to leave.\n".encode("utf-8"))

        while True:
            raw = conn.recv(4096)
            if not raw:
                # Client closed the connection.
                break
            text = raw.decode("utf-8").rstrip("\n")
            if text == "":
                continue
            line = f"[{timestamp()}] {username}: {text}"
            print(line)
            broadcast(line, exclude_conn=conn)

    except (ConnectionResetError, ConnectionAbortedError):
        pass
    finally:
        with clients_lock:
            clients.pop(conn, None)
        conn.close()
        if username:
            leave_msg = f"[{timestamp()}] *** {username} has disconnected ***"
            print(leave_msg)
            broadcast(leave_msg)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Chat server listening on {HOST}:{PORT} (Ctrl+C to stop)")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()

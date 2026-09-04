"""
client.py
Beginner-tier chat client. Connects to server.py over localhost, then
runs one thread to receive messages and prints them with their
server-applied timestamp, while the main thread reads your input and
sends it. Type /quit to disconnect gracefully.
"""

import socket
import threading

HOST = "127.0.0.1"
PORT = 5555


def receive_messages(sock):
    while True:
        try:
            data = sock.recv(4096)
        except OSError:
            break
        if not data:
            print("\n[Disconnected from server]")
            break
        print(data.decode("utf-8"), end="")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{PORT}. Is server.py running?")
        return

    # Handshake: server asks for a username first.
    prompt = sock.recv(1024).decode("utf-8")
    print(prompt, end="")
    username = input()
    sock.sendall(username.encode("utf-8"))

    receiver = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver.start()

    try:
        while True:
            text = input()
            if text.strip().lower() == "/quit":
                break
            sock.sendall(text.encode("utf-8"))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sock.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()

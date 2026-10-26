"""
EcoLoop application entry point.
Run with:  flask run  or  python run.py
"""
import os
import socket
from app import create_app

app = create_app()

def find_available_port(default_port=5000):
    env_port = os.environ.get("PORT")
    if env_port:
        return int(env_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", default_port)) != 0:
            return default_port
    return 5001

if __name__ == "__main__":
    port = find_available_port(5000)
    print(f"Starting EcoLoop server on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)

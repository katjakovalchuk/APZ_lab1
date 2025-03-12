"""
This script implements a server Messaging that returns a static message
"""

import socket
from flask import Flask
import requests

PORT = 8051

app = Flask(__name__)


@app.route("/messages", methods=["GET"])
def get_messages():
    """
    A function that works with a GET request
    """
    return "not implemented yet\n"


async def register_service_in_config_server():
    """
    This function makes a request to the Config Server to register the service
    """
    hostname = socket.gethostbyname(socket.gethostname())
    service_data = {"service_name": "messages-service", "ip": f"{hostname}:{PORT}"}

    try:
        requests.post("http://localhost:5000/register", json=service_data)
    except requests.exceptions.RequestException as e:
        print(f"Failed to register logging-service: {e}")


if __name__ == "__main__":
    print(f"Starting Messages Service on port {PORT}...")
    app.run(port=PORT)

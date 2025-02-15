"""
This script implements a server Messaging that returns a static message
"""

from flask import Flask

app = Flask(__name__)


@app.route("/messages", methods=["GET"])
def get_messages():
    """
    A function that works with a GET request
    """
    return "not implemented yet\n"


if __name__ == "__main__":
    print("Starting Messages Service on port 8051...")
    app.run(port=8051)

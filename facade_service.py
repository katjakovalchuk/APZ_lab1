"""
This script implements the facade pattern,
which is accessed by a user with a POST or GET and, 
depending on the type of request, the required service 
is called - Logging or Messages
"""

from flask import Flask, request, jsonify
import uuid
import grpc
import login_pb2
import login_pb2_grpc
import requests
import time

app = Flask(__name__)


class FacadeService:
    """
    This class implements the Facade pattern
    """

    def __init__(self):
        self.channel = grpc.insecure_channel("127.0.0.1:50061")
        self.stub = login_pb2_grpc.LoggingServiceStub(self.channel)

    def save_msg(self, msg):
        """
        This function implements sending a message to the Logging service.
        """
        msg_uuid = str(uuid.uuid4())
        request = login_pb2.PostMessageRequest(uuid=msg_uuid, msg=msg)
        retries = 5
        attempt = 0

        while attempt < retries:
            try:
                print(f"Attempting to send message: {msg} (Attempt {attempt + 1})")
                # if attempt < 3:
                #     raise grpc.RpcError("Simulated connection error")

                response = self.stub.PostMessage(request)
                print(f"Response received: {response}")
                return response.success

            except grpc.RpcError as e:
                print(f"gRPC error details: {e}")

                attempt += 1
                if attempt < retries:
                    print(f"Attempt {attempt} failed, retrying...")
                    time.sleep(2)
                else:
                    print(f"Failed after {retries} attempts: {e}")
                    return False

        return False

    def get_all_messages(self):
        """
        This function will ask the Logging and Messages services to return a message.
        """
        logging_response = self.stub.GetAllMessages(login_pb2.GetMessageRequest())
        messages_logging = logging_response.message
        messages_text = ""
        try:
            messages_response = requests.get(
                "http://localhost:8051/messages", timeout=2
            )
            messages_text = messages_response.text
        except requests.exceptions.Timeout:
            messages_text = "Timeout: Messages Service dont respond."

        return f"{messages_logging}\n{messages_text}"


facade = FacadeService()


@app.route("/message", methods=["POST"])
def handle_post():
    """
    A function that works with a POST request
    """
    msg = request.json.get("msg")
    if not msg:
        return jsonify({"error": "No message provided"}), 400

    success = facade.save_msg(msg)
    return jsonify({"success": success})


@app.route("/messages", methods=["GET"])
def handle_get():
    """
    A function that works with a GET request
    """
    messages = facade.get_all_messages()
    return messages


if __name__ == "__main__":
    print("Starting Facade Service on port 8046")
    app.run(port=8046)

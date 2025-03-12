"""
This script implements the facade pattern,
which is accessed by a user with a POST or GET and, 
depending on the type of request, the required service 
is called - Logging or Messages
"""

import uuid
import requests
import time
import random
from flask import Flask, request, jsonify
import grpc
import logging_pb2
import logging_pb2_grpc

app = Flask(__name__)


class FacadeService:
    """
    This class implements the Facade pattern
    """

    def __init__(self):
        self.logging_services = self.get_all_logging_services()

    def get_all_logging_services(self):
        try:
            responce_from_config = requests.get(
                "http://localhost:5000/services/logging-service"
            )
            if responce_from_config.status_code != 200:
                print(
                    f"Failed to retrieve services: {responce_from_config.status_code}"
                )
                return []
            logging_services = responce_from_config.json().get("instances", [])
            print(f"Get list of logging services: {logging_services}")
            return logging_services
        except requests.exceptions.RequestException as e:
            print(f"Error getting logging services: {e}")
            return []

    def get_random_service(self):
        if not self.logging_services:
            self.logging_services = self.get_all_logging_services()
        if not self.logging_services:
            raise Exception("There is not any logging service available")

        selected_service = random.choice(self.logging_services)
        print(f"Selected Service: {selected_service}")
        channel = grpc.insecure_channel(selected_service)
        return logging_pb2_grpc.LoggingServiceStub(channel)

    def save_msg(self, msg):
        """
        This function implements sending a message to the Logging service.
        """
        msg_uuid = str(uuid.uuid4())
        request_ = logging_pb2.PostMessageRequest(uuid=msg_uuid, msg=msg)
        retries = 5
        attempt = 0

        while attempt < retries:
            try:
                random_service = self.get_random_service()
                print(f"Attempting to send message: {msg} (Attempt {attempt + 1})")
                response = random_service.PostMessage(request_)
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
        This function will ask the Logging and Messages services
        to return a message.
        """
        logging_text = ""
        try:
            random_service = self.get_random_service()
            logging_response = random_service.GetAllMessages(
                logging_pb2.GetMessageRequest()
            )
            logging_text = logging_response.message
        except requests.exceptions.Timeout:
            logging_text = "Timeout: Logging Service dont respond."

        messages_text = ""
        try:
            messages_response = requests.get(
                "http://localhost:8051/messages", timeout=2
            )
            messages_text = messages_response.text
        except requests.exceptions.Timeout:
            messages_text = "Timeout: Messages Service dont respond."

        return f"{logging_text}\n{messages_text}"


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

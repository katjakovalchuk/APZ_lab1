"""
this Python script implements a login service to accept a pair of 
{uuid, message} and save them to a local hash table, 
where the key is the hash of the message.
"""

import asyncio
import hashlib
import grpc
import logging_pb2
import logging_pb2_grpc
import hazelcast
import requests
import socket
import argparse


class MessageStorage:
    """
    This class is used to store notifications that we receive
    """

    def __init__(self, hazelcast_client):
        self.client = hazelcast_client
        self.message_map = self.client.get_map("messages").blocking()

    def save_message(self, uuid, message):
        """
        This function is designed to store
        messages that we receive in a pair {hash, message}.
        """
        message_hash = hashlib.sha256(f"{message}".encode("utf-8")).hexdigest()

        if not self.message_map.contains_key(message_hash):
            self.message_map.put(message_hash, message)
            return True
        else:
            return False

    def get_all_messages(self):
        """
        Function returns all messages from the message_table
        """
        return " ".join(self.message_map.values())


class LoggingService(logging_pb2_grpc.LoggingServiceServicer):
    """
    This class implements the Logging service that accepts
    messages and saves them or returns them.
    """

    def __init__(self, hazelcast_client):
        self.message_storage = MessageStorage(hazelcast_client)

    async def PostMessage(self, request, context):
        """
        An asynchronous function that saves messages in a
        hazelcast map and returns True if the message was saved successfully,
        False if not.
        """
        success = self.message_storage.save_message(request.uuid, request.msg)
        if success:
            print(f"Message received: {request.msg}")
        return logging_pb2.PostMessageSuccess(success=True)

    async def GetAllMessages(self, request, context):
        """
        An asynchronous function that returns all messages from a hazelcast map.
        """
        messages = self.message_storage.get_all_messages()
        return logging_pb2.GetMessageResponce(message=messages)


async def register_service_in_config_server(port):
    """
    This function makes a request to the Config Server to register the service
    """
    hostname = socket.gethostbyname(socket.gethostname())
    service_data = {"service_name": "logging-service", "ip": f"{hostname}:{port}"}

    try:
        await asyncio.to_thread(
            lambda: requests.post("http://localhost:5000/register", json=service_data)
        )
        print("Service registered successfully")
    except requests.exceptions.RequestException as e:
        print(f"Failed to register logging-service: {e}")


async def run_server(port):
    """
    An asynchronous function that starts and runs
    the server until we stop it with Ctrl+Z.
    """
    print(f"Starting gRPC server on port {port}...")
    hazelcast_client = hazelcast.HazelcastClient(
        cluster_name="dev",
    )
    map = hazelcast_client.get_map("wiwiwi").blocking()
    print("Hazelcast client initialized successfully")
    await register_service_in_config_server(port)
    server = grpc.aio.server()
    logging_pb2_grpc.add_LoggingServiceServicer_to_server(
        LoggingService(hazelcast_client), server
    )
    server.add_insecure_port(f"0.0.0.0:{port}")
    await server.start()
    print(f"Server started on {port}, waiting for connections...")
    await server.wait_for_termination()


def parse_arguments():
    """
    This function parses command line arguments to get 
    the port on which to run the service.
    """
    parser = argparse.ArgumentParser(description="Start a logging service server")
    parser.add_argument(
        "--port", type=int, required=True, help="Port number to run the server on"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(run_server(args.port))

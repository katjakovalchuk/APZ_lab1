"""
this Python script implements a login service to accept a pair of 
{uuid, message} and save them to a local hash table, 
where the key is the hash of the message.
"""

import asyncio
import grpc
import login_pb2
import login_pb2_grpc
import hashlib


class MessageStorage:
    """
    This class is used to store notifications that we receive
    """

    def __init__(self):
        self.message_table = {}

    def save_message(self, uuid, message):
        """
        This function is designed to store
        messages that we receive in a pair {hash, message}.
        """
        message_hash = hashlib.sha256(f"{message}".encode("utf-8")).hexdigest()

        if message_hash not in self.message_table:
            self.message_table[message_hash] = message
            return True
        else:
            return False

    def get_all_messages(self):
        """
        Function returns all messages from the message_table
        """
        return " ".join(self.message_table.values())


class LoggingService(login_pb2_grpc.LoggingServiceServicer):
    """
    This class implements the Logging service that accepts
    messages and saves them or returns them.
    """

    def __init__(self):
        self.message_storage = MessageStorage()

    async def PostMessage(self, request, context):
        """
        An asynchronous function that saves messages in a
        hash table and returns true if the message was saved successfully,
        False if not.
        """
        success = self.message_storage.save_message(request.uuid, request.msg)
        if success:
            print(f"Message received: {request.msg}")
        return login_pb2.PostMessageSuccess(success=True)

    async def GetAllMessages(self, request, context):
        """
        An asynchronous function that returns all messages from a table.
        """
        messages = self.message_storage.get_all_messages()
        return login_pb2.GetMessageResponce(message=messages)


async def run_server():
    """
    An asynchronous function that starts and runs
    the server until we stop it with Ctrl+Z.
    """
    print("Starting gRPC server on port 50061...")
    server = grpc.aio.server()
    login_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingService(), server)
    server.add_insecure_port("0.0.0.0:50061")
    await server.start()
    print("Server started, waiting for connections...")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(run_server())

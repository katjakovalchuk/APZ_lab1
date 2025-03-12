"""
This Python script starts the Config Server, 
which registers the addresses of the Logging and Messages services. 
It is used by facade when reading and writing messages from these services.
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

services = {"logging-service": [], "messages-service": []}


@app.route("/register", methods=["POST"])
def register_service():
    """
    This function registers the service when
    accessing the address 'http://localhost:5000/register'
    """
    data = request.json
    service_name = data.get("service_name")
    ip = data.get("ip")

    if not service_name or not ip:
        return jsonify({"error": "Missing service_name or ip"}), 400

    if service_name not in services:
        return jsonify({"error": "Unknown service"}), 400

    if ip not in services[service_name]:
        services[service_name].append(ip)

    return jsonify({"message": "Service registered successfully!"})


@app.route("/deregister", methods=["POST"])
def deregister_service():
    """
    This function removes the service (for example, if we have disabled it)
    when accessing the address 'http://localhost:5000/deregister'
    """
    data = request.json
    service_name = data.get("service_name")
    ip = data.get("ip")

    if not service_name or not ip:
        return jsonify({"error": "Missing service_name or ip"}), 400

    if service_name in services and ip in services[service_name]:
        services[service_name].remove(ip)
        return jsonify({"message": "Service deregistered successfully"})

    return jsonify({"error": "Service not found"}), 404


@app.route("/services/<service_name>", methods=["GET"])
def get_services(service_name):
    """
    This function returns all services registered in the Config Server
    """
    if service_name not in services:
        return jsonify({"error": "Unknown service"}), 400
    return jsonify({"instances": services[service_name]})


if __name__ == "__main__":
    print("Starting Config Server on port 5000")
    app.run(port=5000)

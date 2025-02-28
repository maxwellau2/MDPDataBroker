from bluetooth import *
import os
import time

# Restart Bluetooth services before starting
os.system("sudo pkill -f rfcomm")
os.system("sudo systemctl restart bluetooth")
os.system("sudo hciconfig hci0 piscan")

server_sock = BluetoothSocket(RFCOMM)
server_sock.bind(("", PORT_ANY))
server_sock.listen(1)
port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
advertise_service(server_sock, "MDP-Server",
                  service_id=uuid,
                  service_classes=[uuid, SERIAL_PORT_CLASS],
                  profiles=[SERIAL_PORT_PROFILE],
                  )

print("Waiting for connection on RFCOMM channel %d" % port)

while True:
    try:
        client_sock, client_info = server_sock.accept()
        print("Accepted connection from ", client_info)

        while True:
            try:
                print("In while loop...")
                data = client_sock.recv(1024)
                if len(data) == 0:
                    print("Client disconnected gracefully.")
                    break  # Exit the loop and wait for a new connection

                print(f"Received [{data}]")
                client_sock.send(data + b" i am pi!")  # Send response

            except IOError as e:
                print(f"Connection error: {e}")
                break  # Client disconnected or connection failed

        print("Client disconnected. Waiting for a new connection...")

    except BluetoothError as e:
        print(f"Bluetooth error: {e}")
        print("Restarting Bluetooth and retrying...")
        os.system("sudo systemctl restart bluetooth")
        time.sleep(5)

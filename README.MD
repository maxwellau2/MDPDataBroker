# Message Broker

This is a simple message broker that can be used to send and receive messages between different processes.

# Setup

1. Install Python 3.8 or higher
2. Setup a virtual environment:

```bash
python -m venv venv
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Run the main script:

```bash
python main.py
```

# Steps to connect bluetooth
```
sudo rfcomm release 0 # release the rfcomm port
sudo rfcomm watch hci0 # watch the rfcomm port, wait for connection
```
Doesn't work? cry then lol
```
# check rfcomm
ls -l /dev/rfcomm*
# don't see anything? bind it urself
sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX 1
# dk mac address?
bluetoothctl paired-devices

# check if rfcomm is used in another process?
ps aux | grep rfcomm

sudo lsof /dev/rfcomm0
sudo kill -9 <PID>

sudo systemctl restart bluetooth


```

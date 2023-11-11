# ev MQTT script(s)

* Python script to fetch data from various EV APIs and publish their SoC to MQTT
* Meter definition for the cFos PowerBrain wallbox, so that loading rules can utilize the SoC of plugged-in vehicles.

# Installation
```
pip install paho-mqtt PyZE
```

Make sure to have a MQTT broker (like mosquitto) available to connect to.

Then set the right hostnames or ip addresss and ports in config.py as well as credentials in secrets.py

To start and test if it works, run:

```
python3 zoe-connector.py
```

The scripts will run in an infinite loop until an error happens or they are aborted via Ctrl+C.

To have it started on system startup on a Linux-/Debian-based system, create a file zoe.service in /etc/systemd/system:
```
[Unit]
Description=Zoe stream SoC to MQTT
Documentation=https://github.com/domsom/ev-mqtt-connectors
After=network.target mosquitto.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=envoy
Group=envoy
ExecStart=/usr/bin/python3 /path/to/zoe-connector.py
WorkingDirectory=/path-to-zoe-connector.py
Environment=PYTHONUNBUFFERED=true
Restart=always
RestartSec=5
SyslogIdentifier=zoe
StandardError=journal

[Install]
WantedBy=multi-user.target
```
Adjust the two directories to where you put the script, then run:
```
sudo systemctl daemon-reload
sudo systemctl enable zoe.service 
sudo systemctl start zoe.service
```

# Acknowledgement
* @akleber for publishing the script, enabling me to fast forward these adjustments within just an hour or so :-)

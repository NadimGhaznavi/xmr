---
layout: post
title: Monero XMR Mining Configuration for Kermit
date: 2024-09-05
---

# Introduction and Scope

This page documents the specific deployment of the software that is deployed on one subnet, behind one upnp capable router. I am running two full Monero nodes on the same subnet. Therefore some port numbers for Internet facing services use non-standard port numbers. This is to ensure that the router knows where to send inbound data requests.

This page documents the configuration on Kermit, the primary node hosting the full Monero Blockchain, a P2Pool Daemon and a XMRig miner.

# Hosts, Services and Ports

| Service                  | Description | Value                    |
|--------------------------| ------------| -------------------------|
| Monero daemon on kermit  | ZMQ PUB     | port 20083               |
| Monero daemon on kermit  | ZMQ RPC     | port 20082               |
| Monero daemon on kermit  | P2P BIND    | port 20080               |
| Monero daemon on kermit  | RPC BIND    | port 20081               |
| P2Pool daemon on kermit  | STRATUM     | port 3333                |
| P2Pool daemon on kermit  | ZMQ PUB     | port 20083               |
| P2Pool daemon on kermit  | ZMQ RPC     | port 20081               |
| P2Pool daemon on kermit  | P2P         | port 38889               |
| P2Pool daemon on kermit  | HOST        | 192.168.0.176 (kermit)   |
| XMRig miner on kermit    | ZMQ         | port 18082               |
| XMRig miner on kermit    | HTTP        | port 8888                |
| XMRig miner on kermit    | URL         | kermit.osoyalce.com:3333 |


# Running the P2Pool Daemon as a Service

I authored the wrapper script to actually start P2Pool, but I found the solution to using a named pipe and P2Pool service definition in this [Reddit post](https://www.reddit.com/r/MoneroMining/comments/12w28m6/comment/jhffnn8/?utm_source=share&utm_medium=web2x&context=3&rdt=38081) by [Krewlar](https://www.reddit.com/user/krewlar/). Kudos to [Krewlar](https://www.reddit.com/user/krewlar/) for doing the heavy lifting for this solution.

## Systemd Service Definitions to run P2Pool as a service

This solution uses two distinct systemd files to start P2Pool.

A socket service that creates a named pipe that connects the the P2Pool daemon's standard input. This pipe is used to interact with the daemon once it's running. By using this architecture, you can run processes (e.g. a cron script) to send commands to the P2Pool daemon while still running it as a service.
The actual P2Pool service definition. This definition does not start P2Pool directly, instead it calls a shell script (shown below) that passes in all the options used to start the P2Pool daemon.

## The systemd p2pool.socket definition

This file is installed in `/etc/systemd/system` and is called p2pool.socket. A full listing of the file is shown below:

```
[Unit]
Description=P2Pool Socket

[Socket]
ListenFIFO=/opt/prod/p2pool/p2pool.stdin
RemoveOnStop=true

[Install]
WantedBy=sockets.target
```

## The systemd p2pool.service Definition

This file is installed in `/etc/systemd/system` and is called p2pool.service. A full listing of the file is shown below:

```
[Unit]
Description=P2Pool Full Node
After=network.target p2pool.socket
#Requires=monerod.service
BindsTo=p2pool.socket

[Service]
StandardInput=socket
Sockets=p2pool.socket
WorkingDirectory=/opt/prod/p2pool/
Type=simple
Restart=always
ExecStartPre=sysctl vm.nr_hugepages=3072
ExecStart=/opt/prod/p2pool/start-p2pool-mini.sh
TimeoutStopSec=60
StandardOutput=file:/opt/prod/p2pool/p2pool.log
StandardError=file:/opt/prod/p2pool/p2pool.err
[Unit]
Description=P2Pool Full Node
After=network.target p2pool.socket
#Requires=monerod.service
BindsTo=p2pool.socket

[Service]
StandardInput=socket
Sockets=p2pool.socket
WorkingDirectory=/opt/prod/p2pool/
Type=simple
Restart=always
ExecStartPre=sysctl vm.nr_hugepages=3072
ExecStart=/opt/prod/p2pool/start-p2pool-mini.sh
TimeoutStopSec=60
StandardOutput=file:/opt/prod/p2pool/p2pool.log
StandardError=file:/opt/prod/p2pool/p2pool.err

[Install]
WantedBy=multi-user.target

[Install]
WantedBy=multi-user.target
```

## Activing and Enabling the P2Pool Service

To refresh systemd's configuration after creating the service and socket definitions use the command below:

```
sudo systemd daemon-reload
```

To have the P2Pool daemon automatically start at boot time use the command below:

```
sudo systemd enable p2pool.service
```

To actually start the service without rebooting use the command below:

```
sudo systemd start p2pool.service
```

## The P2Pool Daemon Startup Script

I use a shell script to start the P2Pool Daemon. A few points about the startup script:

* The script is not run directly, it's used by a systemd service
* P2Pool is configured to mine on the mini sidechain (the `--mini` switch)
* Be sure to substitute your own Monero wallet address for the WALLET variable
* The `MONERO_NODE` is the IP of a machine that hosts the Monero Blockchain i.e. runs the monerod daemon
* The `ZMQ_PORT` and `RPC_PORT` need to match what the monerod daemon's configuration
* The `P2P_DIR` is the directory where you have the P2Pool software installed


This section shows the start script used to launch P2Pool daemon.

```
#!/bin/bash

# kermit
MONERO_NODE="192.168.0.176"

ANY_IP="0.0.0.0"
STRATUM_PORT=3333
P2P_PORT=38889
ZMQ_PORT=20083
RPC_PORT=20081
P2P_DIR="/opt/prod/p2pool"
WALLET="******************************************************************"
LOG_LEVEL=0
IN_PEERS=10
OUT_PEERS=10
DATA_API_DIR="${P2P_DIR}/json"
P2P_LOG="${P2P_DIR}/p2pool.log"

USER=$(whoami)
if [ "$USER" != "root" ]; then
        echo "ERROR: Run the p2pool daemon as root, exiting.."
        exit 1
fi

./p2pool \
        --host ${MONERO_NODE} \
        --wallet ${WALLET} \
        --mini \
        --stratum ${ANY_IP}:${STRATUM_PORT} \
        --p2p ${ANY_IP}:${P2P_PORT} \
        --rpc-port ${RPC_PORT} \
        --zmq-port ${ZMQ_PORT} \
        --loglevel ${LOG_LEVEL} \
        --in-peers ${IN_PEERS} \
        --out-peers ${OUT_PEERS} \
         | tee -a ${P2P_LOG}
```

# Monero Daemon Startup Script on Kermit

This section documents the startup script used to launch the Monero daemon on Kermit.

```
#!/bin/bash

### User defined variables

# Bind to all available network interfaces
IP_ALL="0.0.0.0"

# Port numbers
ZMQ_PUB_PORT="20083"
ZMQ_RPC_PORT="20082"
P2P_BIND_PORT="20080"
RPC_BIND_PORT="20081"
PRIORITY_NODE_PORT="18080"

# Peer limits
OUT_PEERS="10"
IN_PEERS="10"

# Log settings
LOG_LEVEL="0"
MAX_LOG_FILES="5"
MAX_LOG_SIZE="100000"
LOG_NAME="monerod.log"

# Not sure
SHOW_TIME_STATS="1"

# Where the blockchain (lmdb directory) is stored
DATA_DIR="/opt/prod/monero-blockchain"

# Trusted Monero nodes to sync off
PRIORITY_NODE_1="p2pmd.xmrvsbeast.com"
PRIORITY_NODE_2="nodes.hashvault.pro"

### End of user defined variables

MONEROD_DIR=/opt/prod/monerod
MONERO_GUI_DIR=/opt/prod/monero-gui
MONERO_CLI_DIR=/opt/prod/monero-cli

# Find the monerod daemon
if [ -d $MONEROD_DIR ]; then
        MONERO_DIR=$MONEROD_DIR
elif [ -d $MONERO_GUI_DIR ]; then
        MONERO_DIR=$MONERO_GUI_DIR
elif [ -d $MONERO_CLI_DIR ]; then
        MONERO_DIR=$MONERO_CLI_DIR
else
        echo "ERROR: Unable to locate the monerod daemon, exiting..."
        exit 1
fi

# Set the log name for monerod
LOG_NAME="${MONERO_DIR}/${LOG_NAME}"

# Make sure the daemon is being run as root
USER=$(whoami)
if [ "$USER" != "root" ]; then
        echo "ERROR: Run the monerod daemon as root, exiting.."
        exit 1
fi

# Launch the monerod daemon
$MONERO_DIR/monerod \
        --zmq-pub tcp://${IP_ALL}:${ZMQ_PUB_PORT} \
        --zmq-rpc-bind-ip ${IP_ALL} --zmq-rpc-bind-port ${ZMQ_RPC_PORT} \
        --p2p-bind-ip ${IP_ALL} --p2p-bind-port ${P2P_BIND_PORT} \
        --add-priority-node=${PRIORITY_NODE_1}:${P2P_BIND_PORT} \
        --add-priority-node=${PRIORITY_NODE_2}:${P2P_BIND_PORT} \
        --rpc-bind-ip ${IP_ALL} --rpc-bind-port ${RPC_BIND_PORT} --restricted-rpc \
        --confirm-external-bind \
        --data-dir ${DATA_DIR} \
        --out-peers ${OUT_PEERS} --in-peers ${IN_PEERS} \
        --disable-dns-checkpoints --enable-dns-blocklist \
        --log-file ${MONERO_DIR}/monerod.txt \
        --log-level ${LOG_LEVEL} --max-log-files ${MAX_LOG_FILES} \
        --max-log-file-size ${MAX_LOG_SIZE} \
        --show-time-stats ${SHOW_TIME_STATS} \
        --igd enabled \
        --max-connections-per-ip 1 \
        --db-sync-mode safe
```


---
layout: post
title: Monero Daemon Configuration 
date: 2025-05-22
---

# Table of Contents

* [Introduction and Scope](#introduction-and-scope)
* [Pre-Requisites](#pre-requisites)
  * [Linux Operating System](#linux-operating-system)
  * [Disk Space Requirements](#disk-space-requiements)
  * [bzip2](#bzip2)
* [Download and Install the Monero Daemon Software](#download-and-install-the-monero-daemon-software)
* [The start-monerod.sh Script](#the-start-monerod.sh-script)
* [The Actual Blockchain](#the-actual-blockchain)
* [Configuring the Monero Daemon to Run as a Service](#configuring-the-monero-daemon-to-run-as-a-service)
  * [Configuring the Monero Daemon Service](#configuring-the-monero-daemon-service)
  * [Configuring the Monero Socket Service](#configuring-the-monero-socket-service)
  * [Refreshing systemd and Configuring systemd to run the Monero Daemon at Boot Time](#refreshing-systemd-and-configuring-systemd-to-run-the-monero-daemon-at-boot-time)

# Introduction and Scope

This page documents the configuration of the Monero XMR Daemon (`monerod`) as a system service. Configuring 
`monerod` as a service ensures that it starts automatically whenever the host computer boots up. The Monero
daemon supports interactive commands and to take advantage of this interactive aspect of the daemon I have
configured a named pipe or Unix socket that allows for this. With this configuration you can send commands
to the Monero daemon by echoing commands into the named pipe.

# Pre-Requisites

## Linux Operating System

I am running [Debian](https://debian.org), but these instructions apply to basically any machine running
Linux. 

## Disk Space Requirements

The disk space required to house the full Monero blockchain is significant. As of the writing of this
article, September 26, 2024, the full monero blockchain is 206 Gb. It's recommended that you use a SSD
hard-drive, but I'm a traditional magnetic spinning disk. I migrated from an SSD to this spinning disk
and didn't notice any degradation of mining performance.

## bzip2

The *Monero GUI Wallet* maintainers use `bzip2` to compress their software. This isn't part of the
default Debian install, but can be easily downloaded and installed using `sudo apt install bzip2`.

# Download and Install the Monero Daemon Software

The Monero GUI Wallet includes the Monero Daemon. It's very important that you download this software from
the official source, the [GetMonero.org](https://getmonero.org). You can navigate to their
[Downloads](https://www.getmonero.org/downloads/) page and download the software from there. I image you 
could download the *Monero CLI Wallet* instead, but since I use the *Monero GUI Wallet* as my primary 
Wallet for Monero XMR, that's the software I chose.

Once you've naviaged to the [Downloads](https://www.getmonero.org/downloads/) page, click on the 
[Linux 64-bit](https://downloads.getmonero.org/gui/linux64) link to start the download. When the
download finishes you'll end up with a compressed tarball. As of the writing of this article the
actual file was called `monero-gui-linux-x64-v0.18.3.4.tar.bz2`. As newer versions of the
*Monero GUI Wallet* are released, the version number will change, but I'll use that filename in this
documentation.

I run custom software out of the `/opt` directory on my computers and I use `/opt/prod`, `/opt/qa`,
`/opt/dev` to house *production*, *test* and *development* versions of software. As this is production
software, I will install it into `/opt/prod`. The commands below show me uncompressing and then
untarring the software. I use `gzip` as my preferred compression software and I keep copies of the
original software in `/opt/src`, even if it's not source code. The commands below assume that 
the software was downloaded in the *sally* user's *Downloads* directory.

```
sudo mkdir -p /opt/src/monero-gui-wallet
sudo mv ~sally/Downloads/monero-gui-linux-x64-v0.18.3.4.tar.bz2 /opt/src/monero-gui-wallet
sudo bzip -d /opt/src/monero-gui-wallet/monero-gui-linux-x64-v0.18.3.4.tar.bz2
sudo mkdir /opt/prod
cd /opt/prod
sudo tar xvf /opt/src/monero-gui-wallet/monero-gui-linux-x64-v0.18.3.4.tar
sudo gzip /opt/src/monero-gui-wallet/monero-gui-linux-x64-v0.18.3.4.tar
sudo ln -s monero-gui-v0.18.3.4 monerod
```

When you untar the software, it creates a directory called `monero-gui-v0.18.3.4`. The last command,
above, creates a symbolic link, or shortcut, to the `monero-gui-v0.18.3.4` called `monerod`. This
shortcut is referenced by the system service file definition (described below). By creating and 
using this shortcut you can easily upgrade your *Monero GUI Wallet*, delete the shortcut, and then
re-create it without needing to update your system service definition file.

# The start-monerod.sh Script

The *Monero Daemon* has a lot of command switches. I've created a simple script that stores all
the switches and their values. You'll want to create this script using your favorite editor.
As the *root* user create the script in the `/opt/prod/monerod` directory. A complete listing is 
shown below.

A few things to note about this script.

* I run two full monero nodes on my network which are in the same subnet and are behind the
same router. The router supports upnp for routing inbound traffic. In order for the router to
differentiate between the two nodes each node needs to use unique port numbers. The port numbers
I use in the script below are non-standard, the standard port numbers start with *18* (e.g.
ZMQ_PUB_PORT="18083"). This isn't really relevant, but is worth mentioning in case you encounter
documentation that talks about slightly different port numbers. You can alter these ports again, 
but I don't recommend it.
* You'll note that I have *p2pmd.xmrvsbeast* and *nodes.hashvault.pro* configured with the
`--add-priority-hosts` switch. I trust both of these machines and the people who run the 
Monero nodes on these machines. You can safely remove both of these lines if you prefer. 
* You may also notice that the `DATA_DIR` is set to `/opt/prod/monero-blockchain`, an
explanation for this is covered in the next section.

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
LOG_LEVEL="1"
MAX_LOG_FILES="5"
MAX_LOG_SIZE="100000"
LOG_NAME="monerod.log"

# Not sure
SHOW_TIME_STATS="1"

# Where the blockchain (lmdb directory) is stored
DATA_DIR="/opt/prod/monero-blockchain"

# Where RPC Micro payments go (unused)
WALLET_KEY="48wY7nYBsQNSw7v4Ljo7k3ffNnCtk1YGLNVmPGrW8gVhYQtWJHi6UG3X57JN2ajUSeBcijET8ZzKWYwC3z3Y6fFOO"

# Trusted Monero nodes to sync off
PRIORITY_NODE_1="p2pmd.xmrvsbeast.com"
PRIORITY_NODE_2="nodes.hashvault.pro"

### End of user defined variables

MONEROD_DIR=/opt/prod/monerod

# Find the monerod daemon
if [ -d $MONEROD_DIR ]; then
	MONERO_DIR=$MONEROD_DIR
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
	--add-priority-node=${PRIORITY_NODE_1}:${PRIORITY_NODE_PORT} \
	--add-priority-node=${PRIORITY_NODE_2}:${PRIORITY_NODE_PORT} \
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
	--db-sync-mode safe | tee -a ${LOG_NAME}

```

Once you've created this shell script you'll need to make it executible:

```
sudo chmod a+x /opt/prod/monerod/start-monerod.sh
```

# The Actual Blockchain

I keep the actual blockchain in a different directory than the *Monero Daemon*. This
is referenced by the `--data-dir` switch and the `DATA_DIR` definition in the 
`start-monerod.sh` script described in the previous section. By keeping the blockchain
in a different directory I can download and install a newer version of the
*Monero GUI Wallet*, copy in the `start-monerod.sh` script and fire it up without 
needing to move the 202 Gb file. It also allows you to store that file on another disk
mounted on another directory in case you're using a dedicated SSD drive to house the
blockchain.

You'll need to create this directory:

```
sudo mkdir /opt/prod/monero-blockchain
```

# Configuring the Monero Daemon to Run as a Service

As mentioned in the introduction of this page, the *Monero Daemon* is an interactive 
process that accepts commands. In order to take advantage of this feature while
still running it as a service this implementation uses two distinct services. The
primary service is the actual *Monero Daemon*. The secondary service sets up a named
pipe which allows the user to send commands to the *Monero Daemon* by echoing commands
into the named pipe.

## Configuring the Monero Daemon Service

The *Monero Daemon Service* is configured as a standard systemd service. To do this 
you need to create a systemd service description file in the `/etc/systemd/system` 
directory. Name this file `monerod.service` and create it as the root user. A complete 
listing of this file is shown below.

```
[Unit]
Description=Monero Daemon Full Blockchain Node
After=network.target monerod.socket
BindsTo=monerod.socket

[Service]
StandardInput=socket
Sockets=monerod.socket
WorkingDirectory=/opt/prod/monerod/
Type=simple
Restart=always
ExecStart=/opt/prod/monerod/start-monerod.sh
TimeoutStopSec=60
StandardOutput=file:/opt/prod/monerod/monerod.log
StandardError=file:/opt/prod/monerod/monerod.err

[Install]
WantedBy=multi-user.target
```

A few things to note about the systemd service definition file, above, are:

* The systemd service runs a shell script called `start-monerod.sh`. A complete listing of 
this file's contents is shown in a previous section of this page.
* The service definition relies on a `monerod.socket` service. A description of this `monerod.socket`
service and a complete service definition is shown in the next section.

## Configuring the Monero Socket Service

This service creates a named pipe which allows you to send commands to the *Monero Daemon*
service. Like the *Monero Daemon* service definition, this service definition file should
also be created in the `/etc/systemd/system` directory. A complete listing of the service 
definition file is shown below. Create this file as the *root* user and name it `monerod.socket`.

```
[Unit]
Description=Monerod Stdin Socket

[Socket]
ListenFIFO=/opt/prod/monerod/monerod.stdin
RemoveOnStop=true

[Install]
WantedBy=sockets.target
```

Note that the named pipe is called `/opt/prod/monerod/monerod.stdin`. To send commands to the
*Monero Daemon* simply echo the command and direct the output into this named pipe. The 
shell command below shows an example:

```
echo status > /opt/prod/monerod/monerod.stdin
```

If you look at the previous section where we defined the *Monero Daemon* service, you will
see that it includes a `StandardOutput` directive. The results of the command (e.g. status)
will show up in this file.

## Refreshing systemd and Configuring systemd to run the Monero Daemon at Boot Time

In order to let *systemd* know about these newly created services i.e. monerod.service and
monerod.socket you need to issue the command below:
```
sudo systemd daemon-reload
```

To have *systemd* automatically start the *Monero Daemon* whenever your system boots, simply
execute the command below:
```
sudo systemd enable monerod.service
```

That's it! You're done! You can safely reboot the server to confirm that the Monero daemon starts up automatically at boot time. Check the `/opt/prod/monerod/monerod.log` file for logging information.

You can also start the service without rebooting:

```
sudo systemctl start monerod
```



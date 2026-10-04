---
title: Initial Installation
author_profile: true
layout: single
---

# Initial Installation

`scripts/initial-install.sh` installs XMR Pool on a new Debian-based server. Run it as `root` from a repository checkout. Development is a standalone hot node:

```bash
sudo scripts/initial-install.sh --environment dev
```

QA and production require an initial cluster role:

```bash
sudo scripts/initial-install.sh --environment qa --initial-role hot
sudo scripts/initial-install.sh --environment prod --initial-role cold
```

The target must have `python3` and `apt-get`, `/root/.bmca-leaf` must be installed as `root:root` with mode `0600`, and `/opt/xmr` and `/opt/xmr_ops` must not already exist. Its hostname must belong to the selected environment, and the CA's NFS share must be available at `/imports/bmca_certs`. The installer prompts for the application, replication, admin database, and admin browser passwords. If `/root/.xmr` already contains valid application credentials, they can be reused.

The installer:

- Installs Caddy, MariaDB, compiler, and Python development dependencies.
- Creates restricted `xmr` and `xmr-admin` service accounts.
- Copies the application to `/opt/xmr` and operational scripts to `/opt/xmr_ops`.
- Creates a Python virtual environment and installs `requirements.txt`.
- Creates the MariaDB schema and least-privilege application accounts.
- Installs the `xmr.service` and `xmr-admin.service` systemd units.
- Starts the application on a hot node or configures MariaDB for a cold node.
- Starts the LAN administration service.
- Reads and verifies the environment certificate archive from `/imports/bmca_certs`.
- Requires `/root/.bmca-leaf` and uses it to decrypt the private keys.
- Installs node-specific web and admin certificates, then activates HTTPS in Caddy.
- Enables Caddy-managed public TLS for `xmr.osoyalce.com` on the hot production node.

Credentials and runtime settings are stored under `/opt/xmr/etc`; shared installation credentials are stored in `/root/.xmr` with mode `0600`. To remove the installation and restore the previous Caddy configuration, run `sudo scripts/env-reset.sh`.

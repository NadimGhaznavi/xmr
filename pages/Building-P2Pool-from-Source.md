---
title: "Building P2Pool from Source"
date: 2025-05-22
markdown: GFM
category:
  - Monero XMR 
  - P2Pool
---

# Table of Contents

* [Introduction and Scope](#introduction-and-scope)
* [Install Pre-Requisites](#install-pre-requisites)
* [Download P2Pool from Github](#download-p2pool-from-github)
* [Configure P2Pool](#configure-p2pool)
* [Build P2Pool](#build-p2pool)
* [Links](#links)

---

# Introduction and Scope

This page documents the process of building [SChernykh's P2Pool Software](https://github.com/SChernykh/p2pool).

# Download P2Pool from Github

```
git clone --recursive https://github.com/SChernykh/p2pool
```
# Install Pre-Requisites

On my Debian system:
```
apt update
apt install git build-essential cmake libuv1-dev libzmq3-dev libsodium-dev libpgm-dev libnorm-dev libgss-dev libcurl4-openssl-dev libidn2-0-dev
```

# Configure P2Pool

```
cmake -DWITH_MERGE_MINING_DONATION=OFF ..
```

# Build P2Pool

```
make -j$(nproc)
```

# Links

* [P2Pool on Github](https://github.com/SChernykh/p2pool)
  * [Build Instructions](https://github.com/SChernykh/p2pool/blob/master/README.md#build-instructions)
  * [Disable Auto Donation](https://github.com/SChernykh/p2pool/blob/v4.6/README.md?utm_source=substack&utm_medium=email#donations)

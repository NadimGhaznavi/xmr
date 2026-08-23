---
layout: home
author_profile: true
---

![XMR Logo](/pages/images/xmr_logo.png)

---

# Deployment

Deployment occurs in development, QA, and production environments.

---

## Development Environment

The development environment consists of a single machine.

### Development Server

The following DNS names identify the development environment’s services.

| Component       | Record type | DNS name                     |
|-----------------|-------------|------------------------------|
| Bare-metal host | Hostname    | `sally.osoyalce.com`         |
| Web service     | CNAME       | `xmr-dev.osoyalce.com`       |
| Admin service   | CNAME       | `xmr-admin-dev.osoyalce.com` |
| DB server       | CNAME       | `xmr-db-dev.osoyalce.com`    |

---

## QA Environment

The QA environment has a pair of machines that are a hot/cold cluster.

The cluster uses a DNS name to route traffic.

| Component       | Record type | DNS name               |
|-----------------|-------------|------------------------|
| Cluster Service | CNAME       | `xmr-qa.osoyalce.com`  |

### QA Server 1

| Component       | Record type | DNS name                     |
|-----------------|-------------|------------------------------|
| Bare-metal host | Hostname    | `islands.osoyalce.com`       |
| Web service     | CNAME       | `xmr1-qa.osoyalce.com`       |
| Admin service   | CNAME       | `xmr-admin1-qa.osoyalce.com` |
| DB server       | CNAME       | `xmr-db1-qa.osoyalce.com`    |

### QA Server 2

| Component       | Record type | DNS name                     |
|-----------------|-------------|------------------------------|
| Bare-metal host | Hostname    | `kermit.osoyalce.com`        |
| Web service     | CNAME       | `xmr2-qa.osoyalce.com`       |
| Admin service   | CNAME       | `xmr-admin2-qa.osoyalce.com` |
| DB server       | CNAME       | `xmr-db2-qa.osoyalce.com`    |

---

## Production Environment

The production environment has a pair of machines that are a active/passive cluster.

The cluster uses a DNS name to route traffic.

| Component   | Record type | DNS name            |
|-------------|-------------|---------------------|
| Cluster VIP | CNAME       | `xmr.osoyalce.com`  |


### Production Server 1

| Component       | Record type | DNS name                  |
|-----------------|-------------|---------------------------|
| Bare-metal host | Hostname    | `bama.osoyalce.com`       |
| Web service     | CNAME       | `xmr1.osoyalce.com`       |
| Admin service   | CNAME       | `xmr-admin1.osoyalce.com` |
| DB server       | CNAME       | `xmr-db1.osoyalce.com`    |

### Production Server 2

| Component       | Record type | DNS name                     |
|-----------------|-------------|------------------------------|
| Bare-metal host | Hostname    | `wintermute.osoyalce.com`    |
| Web service     | CNAME       | `xmr2.osoyalce.com`          |
| Admin service   | CNAME       | `xmr-admin2.osoyalce.com`    |
| DB server       | CNAME       | `xmr-db2.osoyalce.com`       |

---

# Implementations

- [P2Pool API](/pages/implementations/p2pool_api.html)
- [P2Pool Log](/pages/implementations/p2pool_log.html)

---

# Use Cases

## System Operator

- [Install XMR Pool software](/pages/use-cases/install-xmr-pool-software.html)
- Configure XMR Pool
- Start XMR Pool service
- Stop XMR Pool service
- Enable XMR Pool service
- Disable XMR Pool service
- Configure two-node cluster
- Fail over to standby node
- Restore primary node
- View system/cluster health

## Account Holder

- Register account
- Sign in
- Sign out
- Manage account
- Register Monero wallet
- Create/manage mining pool
- View pool dashboard
- View worker status and uptime
- View hashrate
- View shares found
- View blocks found
- View payouts
- View fees
- View pool uptime

## Miner / XMRig

- Connect to mining pool
- Authenticate/identify mining worker
- Submit mining work
- Reconnect after interruption
- Administrator
- Access administration dashboard
- View/manage accounts
- View aggregate P2Pool metrics
- View aggregate miner metrics
- View payout metrics
- View fee metrics
- View container/runtime status
- Disable/suspend an account or pool

## XMR Pool system

- Provision P2Pool instance on demand
- Start existing P2Pool instance when miner connects
- Stop idle P2Pool instance
- Collect P2Pool metrics
- Collect miner metrics
- Record payouts
- Calculate/record fees
- Persist metric snapshots
- Replicate database to standby node

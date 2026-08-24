---
title: Deployment
author_profile: true
layout: single
---


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

The QA environment has a pair of machines that are in an active/passive cluster.

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

The production environment has a pair of machines that are in an active/passive cluster.

The cluster uses a DNS name to route traffic.

| Component | Record type | DNS name            |
|-----------|-------------|---------------------|
| Cluster   | CNAME       | `xmr.osoyalce.com`  |


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

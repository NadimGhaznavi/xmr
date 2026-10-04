---
title: Architecture
author_profile: true
layout: single
---

# Architecture

XMR Pool runs in development, QA, and production. Development uses one server; QA and production use two-node active/passive clusters. The installer selects the environment (`dev`, `qa`, or `prod`) and, for clustered environments, the initial role (`hot` or `cold`). The machine hostname supplies its permanent node identity.

Customers access the web application over HTTPS. Caddy terminates TLS, serves static content, and proxies application requests to a systemd-managed service on the local host. Caddy manages the public certificate for the production service name. Locally issued certificates support direct HTTPS testing through node-specific development, QA, and production names.

The LAN-only administration interface runs as a separate systemd service. It has its own hostname and locally issued certificate and is reached through Caddy without exposing the service directly to the Internet.

An account contains a username and Monero wallet. Each account may create up to three pools, one for each supported P2Pool chain: nano, mini, and main. Every pool receives a system-wide unique inbound port stored in MariaDB.

The container manager monitors assigned P2Pool ports. An initial connection triggers creation of a Podman container and is dropped; a subsequent connection is routed to the ready container. Each container runs P2Pool and a scheduled collector that submits telemetry for storage in MariaDB. The web application presents that telemetry to the account holder.

This iteration covers deterministic installation, node-specific HTTPS, application and administration services, and the initial hot/cold configuration.



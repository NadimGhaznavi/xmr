---
layout: post
title: Mining Farm hosts, services and port numbers
date: 2024-06-11
---

# Introduction and Scope

This page documents the specific deployment of the software that is deployed on one subnet, behind oneupnp capable router. As a result, some port numbers of the same Internet facing service is serving data from a non-standard port. This page documents that deployment.

# Hosts, Services and Ports

| Service | Description | Kermit's Ports |
|---------| ------------| ---------------|
| Monero  | ZMQ PUB     | 20083          |
| Monero  | ZMQ RPC     | 20082          |
| Monero  | P2P BIND    | 20080          |
| Monero  | RPC BIND    | 20081          |
| P2Pool  | TODO        |                |
| XMRig   |             |                |

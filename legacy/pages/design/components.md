---
title: Components
author_profile: true
layout: single
---

# Components

## Caddy

Accepts:

- Internet traffic
- LAN traffic


Routes to:

- App server
- Admin server (LAN traffic only)

## App server

Accepts:

- User requests

Read/Write:

- MariaDb
  - Configuration information

## Admin server

Accepts:

- Admin requests

Read/Write:

- MariaDb

## Containerized p2pool data collector

Write:

- MariaDb

## MariaDb

- User accounts (username and wallet) 
- User pool performance data
- User rig performance data
- User share found and payout data
- User fees

- Current:
  - Cluster state
  - List of running containers



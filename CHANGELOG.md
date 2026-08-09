# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [Release 0.2.3] - 2026-08-09 10:53


## [Release 0.2.2] - 2026-08-09 10:41


## [Release 0.2.1] - 2026-08-09 10:38


## [Release 0.2.0] - 2026-08-09 10:25


- Added a new *Admin* server instance with account management capability.

## [Release 0.1.0] - 2026-08-09 08:43


- Install and wipe environment scripts: `env-reset.sh` and `initial-install.sh`
  - Configures Caddy configuration deployment
  - Configures replication between *bama* and *wintermute*, the *hot/cold* pair that make up the cluster
- Built cluster control and support with `cluster-mgr.sh`
  - Report on cluster status and health
  - Support failover
  - Support restart
  - Supports *fail over to*, *promote*, and *demote* features
- App presents 
  - initial *Welcome* screen
  - *Login* screen
  - *New Account* screen, with new account capability
    - Account is stored in MariaDb

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Created `constats/DHost.py` file to track the hosts, roles and environments that make up the app

### Changed

- Replaced `scripts/dhs-report.sh` with a Python version that uses the new `DHost.py` data

---

## [Release 0.3.11] - 2026-08-24 03:47

### Fixed 

- Corrected site URL in `_config.yml`

---

## [Release 0.3.9] - 2026-08-24 03:29

- Cleaned up the website, organized it

---

## [Release 0.3.7] - 2026-08-23 17:19

- Added a `dns-report.sh` script for *DevOps* to sanity check the environment.

---

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

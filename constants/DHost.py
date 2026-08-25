# constants/DHost.py
#
#    Bear & Moose XMR Mining Pool
#    Author: Nadim-Daniel Ghaznavi
#    Copyright: (c) 2024-2026 Nadim-Daniel Ghaznavi
#    GitHub: https://github.com/NadimGhaznavi/xmr
#    License: GPL 3.0


from typing import Final, NamedTuple


class DNSRecord(NamedTuple):
    environment: str
    service: str
    name: str


class DHost:
    # Production Hosts
    BAMA: Final[str] = "bama.osoyalce.com"
    WINTERMUTE: Final[str] = "wintermute.osoyalce.com"
    XMR: Final[str] = "xmr.osoyalce.com"
    XMR1: Final[str] = "xmr1.osoyalce.com"
    XMR2: Final[str] = "xmr2.osoyalce.com"
    XMR_APP1: Final[str] = "xmr-app1.osoyalce.com"
    XMR_APP2: Final[str] = "xmr-app2.osoyalce.com"
    XMR_ADMIN1: Final[str] = "xmr-admin1.osoyalce.com"
    XMR_ADMIN2: Final[str] = "xmr-admin2.osoyalce.com"
    XMR_DB1: Final[str] = "xmr-db1.osoyalce.com"
    XMR_DB2: Final[str] = "xmr-db2.osoyalce.com"

    # QA Hosts
    ISLANDS: Final[str] = "islands.osoyalce.com"
    KERMIT: Final[str] = "kermit.osoyalce.com"
    XMR_QA: Final[str] = "xmr-qa.osoyalce.com"
    XMR1_QA: Final[str] = "xmr1-qa.osoyalce.com"
    XMR2_QA: Final[str] = "xmr2-qa.osoyalce.com"
    XMR_APP1_QA: Final[str] = "xmr-app1-qa.osoyalce.com"
    XMR_APP2_QA: Final[str] = "xmr-app2-qa.osoyalce.com"
    XMR_ADMIN1_QA: Final[str] = "xmr-admin1-qa.osoyalce.com"
    XMR_ADMIN2_QA: Final[str] = "xmr-admin2-qa.osoyalce.com"
    XMR_DB1_QA: Final[str] = "xmr-db1-qa.osoyalce.com"
    XMR_DB2_QA: Final[str] = "xmr-db2-qa.osoyalce.com"

    # Development Host
    SALLY: Final[str] = "sally.osoyalce.com"
    XMR_DEV: Final[str] = "xmr-dev.osoyalce.com"
    XMR_APP_DEV: Final[str] = "xmr-app-dev.osoyalce.com"
    XMR_ADMIN_DEV: Final[str] = "xmr-admin-dev.osoyalce.com"
    XMR_DB_DEV: Final[str] = "xmr-db-dev.osoyalce.com"


class DProdHosts:
    HOST1: Final[str] = DHost.BAMA
    HOST2: Final[str] = DHost.WINTERMUTE
    CLUSTER: Final[str] = DHost.XMR
    WEB1: Final[str] = DHost.XMR1
    WEB2: Final[str] = DHost.XMR2
    APP1: Final[str] = DHost.XMR_APP1
    APP2: Final[str] = DHost.XMR_APP2
    ADMIN1: Final[str] = DHost.XMR_ADMIN1
    ADMIN2: Final[str] = DHost.XMR_ADMIN2
    DB1: Final[str] = DHost.XMR_DB1
    DB2: Final[str] = DHost.XMR_DB2


class DQAHosts:
    HOST1: Final[str] = DHost.ISLANDS
    HOST2: Final[str] = DHost.KERMIT
    CLUSTER: Final[str] = DHost.XMR_QA
    WEB1: Final[str] = DHost.XMR1_QA
    WEB2: Final[str] = DHost.XMR2_QA
    APP1: Final[str] = DHost.XMR_APP1_QA
    APP2: Final[str] = DHost.XMR_APP2_QA
    ADMIN1: Final[str] = DHost.XMR_ADMIN1_QA
    ADMIN2: Final[str] = DHost.XMR_ADMIN2_QA
    DB1: Final[str] = DHost.XMR_DB1_QA
    DB2: Final[str] = DHost.XMR_DB2_QA


class DDevHosts:
    HOST: Final[str] = DHost.SALLY
    WEB: Final[str] = DHost.XMR_DEV
    APP: Final[str] = DHost.XMR_APP_DEV
    ADMIN: Final[str] = DHost.XMR_ADMIN_DEV
    DB: Final[str] = DHost.XMR_DB_DEV


DNS_RECORDS: Final[tuple[DNSRecord, ...]] = (
    DNSRecord("DEV", "Web", DDevHosts.WEB),
    DNSRecord("DEV", "App", DDevHosts.APP),
    DNSRecord("DEV", "Admin", DDevHosts.ADMIN),
    DNSRecord("DEV", "DB", DDevHosts.DB),
    DNSRecord("QA", "Cluster", DQAHosts.CLUSTER),
    DNSRecord("QA", "Web", DQAHosts.WEB1),
    DNSRecord("QA", "App", DQAHosts.APP1),
    DNSRecord("QA", "Admin", DQAHosts.ADMIN1),
    DNSRecord("QA", "DB", DQAHosts.DB1),
    DNSRecord("QA", "Web", DQAHosts.WEB2),
    DNSRecord("QA", "App", DQAHosts.APP2),
    DNSRecord("QA", "Admin", DQAHosts.ADMIN2),
    DNSRecord("QA", "DB", DQAHosts.DB2),
    DNSRecord("PROD", "Cluster", DProdHosts.CLUSTER),
    DNSRecord("PROD", "Web", DProdHosts.WEB1),
    DNSRecord("PROD", "App", DProdHosts.APP1),
    DNSRecord("PROD", "Admin", DProdHosts.ADMIN1),
    DNSRecord("PROD", "DB", DProdHosts.DB1),
    DNSRecord("PROD", "Web", DProdHosts.WEB2),
    DNSRecord("PROD", "App", DProdHosts.APP2),
    DNSRecord("PROD", "Admin", DProdHosts.ADMIN2),
    DNSRecord("PROD", "DB", DProdHosts.DB2),
)

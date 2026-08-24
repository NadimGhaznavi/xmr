# constants/DDefault.py
#
#    Bear & Moose XMR Mining Pool
#    Author: Nadim-Daniel Ghaznavi
#    Copyright: (c) 2024-2025 Nadim-Daniel Ghaznavi
#    GitHub: https://github.com/NadimGhaznavi/xmr
#    License: GPL 3.0


from typing import Final


class DDefault:
    XMR_VERSION: Final[str] = "0.3.10"
    INSTALL_DIR: Final[str] = "/opt/xmr"
    OPS_DIR: Final[str] = "/opt/xmr_ops"
    SERVICE_USER: Final[str] = "xmr"
    SERVICE_GROUP: Final[str] = "xmr"
    OPS_USER: Final[str] = "xmrops"
    OPS_GROUP: Final[str] = "xmrops"
    CLUSTER_NODES: Final[tuple[str, str]] = ("bama", "wintermute")
    TRUSTED_LAN: Final[str] = "192.168.0.0/24"
    ADMIN_HOST: Final[str] = "admin.osoyalce.com"
    ADMIN_PORT: Final[int] = 8484
    PUBLIC_PORT: Final[int] = 8000
    STARTING_P2POOL_PORT: Final[int] = 33333

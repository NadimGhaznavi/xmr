"""Public Bear and Moose XMR ASGI server."""

from web.Interface import Route
from web.Server import Server

ROUTES = {
    ("GET", "/"): Route("AppMgr:index"),
    ("HEAD", "/"): Route("AppMgr:index"),
    ("GET", "/health"): Route("AppMgr:health"),
    ("HEAD", "/health"): Route("AppMgr:health"),
    ("GET", "/login"): Route("AppMgr:login", "login.html"),
    ("HEAD", "/login"): Route("AppMgr:login", "login.html"),
    ("GET", "/signup"): Route("AppMgr:signup", "signup.html"),
    ("HEAD", "/signup"): Route("AppMgr:signup", "signup.html"),
    ("GET", "/dashboard"): Route(
        "AppMgr:dashboard", "dashboard.html", blocking=True, authenticated=True
    ),
    ("HEAD", "/dashboard"): Route(
        "AppMgr:dashboard", "dashboard.html", blocking=True, authenticated=True
    ),
    ("GET", "/pool/new"): Route("AppMgr:new_pool", "new-pool.html", authenticated=True),
    ("HEAD", "/pool/new"): Route(
        "AppMgr:new_pool", "new-pool.html", authenticated=True
    ),
    ("GET", "/pool"): Route(
        "AppMgr:edit_pool", "edit-pool.html", blocking=True, authenticated=True
    ),
    ("HEAD", "/pool"): Route(
        "AppMgr:edit_pool", "edit-pool.html", blocking=True, authenticated=True
    ),
}
ACTIONS = {
    "AppMgr:new_account": Route(
        "AppMgr:new_account",
        "dashboard.html",
        error_template="signup.html",
        blocking=True,
    ),
    "AppMgr:authenticate": Route(
        "AppMgr:authenticate",
        "dashboard.html",
        error_template="login.html",
        blocking=True,
    ),
    "AppMgr:create_pool": Route(
        "AppMgr:create_pool",
        "new-pool.html",
        blocking=True,
        authenticated=True,
    ),
    "AppMgr:update_pool": Route(
        "AppMgr:update_pool",
        "edit-pool.html",
        blocking=True,
        authenticated=True,
    ),
}

app = Server(ROUTES, ACTIONS)

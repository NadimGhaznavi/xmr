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
}
ACTIONS = {
    "AppMgr:new_account": Route(
        "AppMgr:new_account",
        "dashboard.html",
        error_template="signup.html",
        blocking=True,
    ),
}

app = Server(ROUTES, ACTIONS)

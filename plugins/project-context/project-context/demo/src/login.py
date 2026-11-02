def tokenlogin(token):
    return {"authenticated": bool(token), "offline_days": 7}

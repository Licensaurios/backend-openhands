import importlib

from flask_security import (
    current_user,
)

def get_server_status():
    
    return {
        "status": "all systems operational!",
        "dev_status": "working for coffee ☕",
        "version": importlib.metadata.version("server"),
        #"username": current_user.email,
        "is_authenticated": current_user.is_authenticated,
    }

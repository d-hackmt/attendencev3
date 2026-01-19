# Attendence/services/auth_service.py
from Attendence.core.config import get_env

def authenticate_admin(username, password):
    """
    Verifies admin credentials against environment variables.
    """
    admin_user = get_env("ADMIN_USERNAME")
    admin_pass = get_env("ADMIN_PASSWORD")
    return username == admin_user and password == admin_pass

from common_core.generic.random_string import generate_random_string


def generate_username(last_name: str, first_name: str, length: int = 8):
    return f"{first_name[:3]}{last_name[:3]}{generate_random_string(length, True)}"

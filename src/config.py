import os

DEBUG = os.getenv("DEBUG", True)

if DEBUG:
    from dotenv import load_dotenv

    load_dotenv()


class MissingEnvVar(Exception):
    def __init__(self, var_name: str) -> None:
        self.var_name = var_name

    def __str__(self) -> str:
        return f"Missing environment variable '{self.var_name}'"


def get_env_var_or_exc(var_name: str, default_value: str = None) -> str:
    result = os.getenv(var_name, default_value)
    if not result:
        raise MissingEnvVar(var_name)

    return result


DB_USER = get_env_var_or_exc("DB_USER")
DB_PASS = get_env_var_or_exc("DB_PASS")
DB_HOST = get_env_var_or_exc("DB_HOST")
DB_PORT = get_env_var_or_exc("DB_PORT")
DB_NAME = get_env_var_or_exc("DB_NAME")

API_KEY = get_env_var_or_exc("API_KEY")

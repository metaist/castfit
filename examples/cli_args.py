# Example: CLI-like args
from typing import Optional
from pathlib import Path
from castfit import castfit


class Args:
    host: str
    port: int
    timeout: Optional[float]
    log: Path


data = {
    "host": "localhost",
    "port": "8080",
    # "timeout": "5.0" # key can be missing
    "log": "app.log",
}

config = castfit(Args, data)
assert config.host == "localhost"
assert config.port == 8080
assert config.timeout is None
assert config.log == Path("app.log")

# if timeout was present:
data = {"host": "localhost", "port": "8080", "timeout": "5.0", "log": "app.log"}
config = castfit(Args, data)
assert config.host == "localhost"
assert config.port == 8080
assert config.timeout == 5.0
assert config.log == Path("app.log")

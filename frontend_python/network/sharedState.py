from dataclasses import dataclass


@dataclass(slots=True)
class SharedState:
    ip_address: str
    port: int
    name: str

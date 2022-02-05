from dataclasses import dataclass


@dataclass
class Zone:
    name: str
    grace_period: int
    threat_modifier: int

    def __str__(self) -> str:
        return self.name

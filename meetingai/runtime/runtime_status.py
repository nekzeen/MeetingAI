"""États possibles d'un composant Runtime."""

from __future__ import annotations

from enum import Enum, auto


class RuntimeStatus(Enum):
    """Représente l'état de santé d'un provider ou du Runtime global.

    Les valeurs sont ordonnées du meilleur état au plus critique afin de
    faciliter l'agrégation : ``max(statuses, key=lambda s: s.severity)``.
    """

    HEALTHY = ("healthy", 0)
    DEGRADED = ("degraded", 1)
    MISSING = ("missing", 2)
    ERROR = ("error", 3)
    UNKNOWN = ("unknown", 4)

    def __init__(self, label: str, severity: int) -> None:
        """Initialise le membre de l'énumération."""
        self.label = label
        self.severity = severity

    def __str__(self) -> str:
        """Retourne le libellé lisible de l'état."""
        return self.label

    def __lt__(self, other: object) -> bool:
        """Compare deux états selon leur sévérité."""
        if not isinstance(other, RuntimeStatus):
            return NotImplemented
        return self.severity < other.severity

    def __le__(self, other: object) -> bool:
        """Compare deux états selon leur sévérité."""
        if not isinstance(other, RuntimeStatus):
            return NotImplemented
        return self.severity <= other.severity

    def __gt__(self, other: object) -> bool:
        """Compare deux états selon leur sévérité."""
        if not isinstance(other, RuntimeStatus):
            return NotImplemented
        return self.severity > other.severity

    def __ge__(self, other: object) -> bool:
        """Compare deux états selon leur sévérité."""
        if not isinstance(other, RuntimeStatus):
            return NotImplemented
        return self.severity >= other.severity

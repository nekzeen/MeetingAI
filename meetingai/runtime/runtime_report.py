"""Rapport de diagnostic d'un provider Runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_status import RuntimeStatus


@dataclass(frozen=True)
class RuntimeReport:
    """Résultat d'un diagnostic ou d'une opération de maintenance.

    Attributes:
        provider_name: Nom unique du provider concerné.
        status: État du provider après diagnostic ou opération.
        capabilities: Capacités concernées par ce provider.
        message: Message résumé à destination de l'utilisateur ou des logs.
        details: Informations techniques supplémentaires (versions, chemins,
            erreurs, etc.).
    """

    provider_name: str
    status: RuntimeStatus
    capabilities: list[RuntimeCapability] = field(default_factory=list)
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

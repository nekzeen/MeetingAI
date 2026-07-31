"""Actions recommandées par la couche Runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class RuntimeActionType(Enum):
    """Types d'actions qu'un provider peut proposer à l'utilisateur."""

    NONE = auto()
    INSTALL_PACKAGE = auto()
    DOWNLOAD_MODEL = auto()
    START_SERVER = auto()
    CONFIGURE = auto()
    REPAIR = auto()
    RETRY = auto()


@dataclass(frozen=True)
class RuntimeAction:
    """Action suggérée à l'utilisateur pour résoudre un état Runtime.

    Attributes:
        action_type: Type d'action à effectuer.
        provider_name: Nom du provider à l'origine de l'action.
        message: Libellé court destiné à l'utilisateur.
        description: Explication détaillée de l'action.
        available: Indique si l'action peut être exécutée automatiquement.
        requires_user: Indique si l'action nécessite une validation humaine.
        parameters: Paramètres libres (modèle, chemin, commande, etc.).
    """

    action_type: RuntimeActionType
    provider_name: str
    message: str
    description: str = ""
    available: bool = True
    requires_user: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)

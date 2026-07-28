"""Modèle métier représentant un modèle d'intelligence artificielle."""

from dataclasses import dataclass
from enum import Enum


class ModelStatus(Enum):
    """États d'installation d'un modèle IA."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update_available"


@dataclass
class AIModel:
    """Représente un modèle IA référencé par l'application.

    Cette dataclass est utilisée par ``ModelManager`` pour centraliser la
    connaissance des modèles disponibles et installés, indépendamment de leur
    famille (transcription, résumé, OCR, traduction, etc.).

    Attributes:
        id: Identifiant unique du modèle.
        display_name: Nom affiché à l'utilisateur.
        family: Famille de modèles (ex. ``speech_to_text``, ``summary``).
        version: Version du modèle.
        size_bytes: Taille en octets du modèle, si connue.
        language: Langue principale du modèle, si applicable.
        status: État d'installation du modèle.
        install_path: Chemin d'installation local, le cas échéant.
    """

    id: str
    display_name: str
    family: str
    version: str
    size_bytes: int | None
    language: str | None
    status: ModelStatus
    install_path: str | None = None

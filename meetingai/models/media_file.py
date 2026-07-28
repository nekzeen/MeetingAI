"""Modèle métier représentant un fichier média."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MediaType(Enum):
    """Types de médias supportés par l'application."""

    AUDIO = "audio"
    VIDEO = "video"


@dataclass(frozen=True)
class MediaFile:
    """Représentation immuable d'un fichier média.

    Cette dataclass expose les propriétés essentielles d'un fichier audio ou
    vidéo utilisé par l'application. L'immuable évite les modifications
    accidentelles après chargement.

    Attributes:
        path: Chemin absolu du fichier.
        name: Nom du fichier avec son extension.
        extension: Extension normalisée en minuscules avec le point.
        size: Taille du fichier en octets.
        media_type: Type de média (``audio`` ou ``video``).
    """

    path: Path
    name: str
    extension: str
    size: int
    media_type: MediaType

    @property
    def type(self) -> str:
        """Retourne le type de média sous forme de chaîne."""
        return self.media_type.value

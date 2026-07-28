"""Résultat produit par un moteur Speech-To-Text."""

from dataclasses import dataclass
from typing import Any


@dataclass
class TranscriptionResult:
    """Représente le résultat d'une transcription.

    Cette dataclass est retournée par tous les moteurs Speech-To-Text afin
    d'unifier le format de sortie, quelle que soit l'implémentation sous-jacente
    (faster-whisper, whisper.cpp, OpenAI, Azure, Deepgram, etc.).

    Attributes:
        text: Texte transcrit.
        language: Langue détectée ou utilisée (code ISO 639-1).
        duration: Durée du média traité en secondes.
        model: Nom du modèle ou du service utilisé.
        processing_time: Temps d'exécution de la transcription en secondes.
        metadata: Métadonnées additionnelles spécifiques au moteur.
    """

    text: str
    language: str
    duration: float
    model: str
    processing_time: float
    metadata: dict[str, Any]

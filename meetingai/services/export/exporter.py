"""Contrat commun des exporteurs de transcription."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class Exporter(ABC):
    """Interface commune pour exporter une transcription dans un format donné.

    Chaque implémentation concrete doit fournir l'extension de fichier associée
    et implémenter ``export``.
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """Extension de fichier incluant le point (``.txt``, ``.md``...)."""

    @abstractmethod
    def export(self, result: TranscriptionResult, output_path: Path) -> None:
        """Écrit le résultat de transcription au chemin demandé.

        Args:
            result: Résultat de transcription à exporter.
            output_path: Chemin du fichier de sortie.

        Raises:
            RuntimeError: Si l'écriture du fichier échoue.
        """

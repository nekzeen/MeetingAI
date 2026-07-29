"""Exporteur au format texte brut."""

from __future__ import annotations

from pathlib import Path

from meetingai.services.export.exporter import Exporter
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TxtExporter(Exporter):
    """Exporte une transcription dans un fichier texte brut."""

    @property
    def extension(self) -> str:
        """Retourne l'extension ``.txt``."""
        return ".txt"

    def export(self, result: TranscriptionResult, output_path: Path) -> None:
        """Écrit le texte de la transcription dans ``output_path``.

        Args:
            result: Résultat de transcription à exporter.
            output_path: Chemin du fichier texte à créer.

        Raises:
            RuntimeError: Si l'écriture échoue.
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.text, encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(
                f"Échec de l'export TXT vers {output_path} : {exc}"
            ) from exc

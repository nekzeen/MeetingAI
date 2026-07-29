"""Exporteur au format Markdown."""

from __future__ import annotations

from pathlib import Path

from meetingai.services.export.exporter import Exporter
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class MarkdownExporter(Exporter):
    """Exporte une transcription dans un fichier Markdown."""

    @property
    def extension(self) -> str:
        """Retourne l'extension ``.md``."""
        return ".md"

    def export(self, result: TranscriptionResult, output_path: Path) -> None:
        """Écrit la transcription formatée en Markdown.

        Args:
            result: Résultat de transcription à exporter.
            output_path: Chemin du fichier Markdown à créer.

        Raises:
            RuntimeError: Si l'écriture échoue.
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                "# Transcription",
                "",
                "## Métadonnées",
                "",
                f"- **Langue** : {result.language}",
                f"- **Modèle** : {result.model}",
                f"- **Durée** : {result.duration:.2f} s",
                f"- **Temps de traitement** : {result.processing_time:.2f} s",
                "",
                "## Texte",
                "",
                result.text,
                "",
            ]
            output_path.write_text("\n".join(lines), encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(
                f"Échec de l'export Markdown vers {output_path} : {exc}"
            ) from exc

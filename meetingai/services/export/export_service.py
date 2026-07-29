"""Service d'export des transcriptions."""

from __future__ import annotations

from pathlib import Path

from meetingai.services.export.exporter import Exporter
from meetingai.services.export.markdown_exporter import MarkdownExporter
from meetingai.services.export.txt_exporter import TxtExporter
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class ExportService:
    """Registre et orchestre les exporteurs de transcription.

    Ce service suit le pattern Stratégie : chaque format est géré par une
    classe implémentant ``Exporter``. De nouveaux formats peuvent être ajoutés
    sans modifier le code existant via ``register_exporter``.

    Args:
        exporters: Mapping optionnel nom -> instance ``Exporter``.
    """

    _DEFAULT_EXPORTERS: dict[str, Exporter] = {
        "txt": TxtExporter(),
        "markdown": MarkdownExporter(),
    }

    def __init__(
        self,
        exporters: dict[str, Exporter] | None = None,
    ) -> None:
        """Initialise le service avec les exporteurs par défaut."""
        self._exporters: dict[str, Exporter] = dict(
            exporters if exporters is not None else self._DEFAULT_EXPORTERS
        )

    def register_exporter(self, format_name: str, exporter: Exporter) -> None:
        """Enregistre ou remplace un exporteur pour un format donné.

        Args:
            format_name: Identifiant du format (``txt``, ``md``...).
            exporter: Instance de l'exporteur.
        """
        self._exporters[format_name] = exporter

    def supported_formats(self) -> list[str]:
        """Retourne la liste des formats supportés."""
        return sorted(self._exporters.keys())

    def extension_for(self, format_name: str) -> str:
        """Retourne l'extension associée à un format.

        Args:
            format_name: Identifiant du format.

        Returns:
            Extension incluant le point.

        Raises:
            ValueError: Si le format n'est pas supporté.
        """
        exporter = self._exporters.get(format_name)
        if exporter is None:
            raise ValueError(
                f"Format d'export non supporté : {format_name}"
            )
        return exporter.extension

    def export(
        self,
        result: TranscriptionResult,
        output_path: Path,
        format_name: str,
    ) -> None:
        """Exporte ``result`` au format demandé.

        Args:
            result: Résultat de transcription à exporter.
            output_path: Chemin du fichier de sortie.
            format_name: Format d'export (``txt``, ``md``...).

        Raises:
            ValueError: Si le format n'est pas supporté.
            RuntimeError: Si l'écriture du fichier échoue.
        """
        exporter = self._exporters.get(format_name)
        if exporter is None:
            raise ValueError(
                f"Format d'export non supporté : {format_name}"
            )
        exporter.export(result, output_path)

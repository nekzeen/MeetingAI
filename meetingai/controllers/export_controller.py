"""Contrôleur dédié à l'export des transcriptions."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from meetingai.config.config_manager import ConfigManager
from meetingai.services.export.export_service import ExportService
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class ExportController(QObject):
    """Orchestre l'export d'une transcription vers un fichier.

    Le contrôleur conserve le dernier résultat de transcription reçu et
    déclenche son export lorsque l'utilisateur choisit un format. Aucune
    logique d'interface n'est présente ici.

    Args:
        export_service: Service d'export à utiliser.
        config_manager: Gestionnaire de configuration pour le répertoire de sortie.
        parent: QObject parent éventuel.
    """

    export_succeeded = Signal(str)
    export_failed = Signal(str)

    def __init__(
        self,
        export_service: ExportService,
        config_manager: ConfigManager,
        parent: QObject | None = None,
    ) -> None:
        """Initialise le contrôleur d'export."""
        super().__init__(parent)
        self._export_service = export_service
        self._config_manager = config_manager
        self._last_result: TranscriptionResult | None = None

    def on_transcription_ready(self, result: TranscriptionResult) -> None:
        """Conserve le dernier résultat de transcription.

        Args:
            result: Résultat à exporter ultérieurement.
        """
        self._last_result = result

    def export_txt(self) -> None:
        """Exporte la dernière transcription au format TXT."""
        self._export("txt", "transcription")

    def export_markdown(self) -> None:
        """Exporte la dernière transcription au format Markdown."""
        self._export("markdown", "transcription")

    def _export(self, format_name: str, base_name: str) -> None:
        """Réalise l'export du dernier résultat disponible.

        Args:
            format_name: Format d'export (``txt``, ``md``...).
            base_name: Nom de base du fichier de sortie sans extension.
        """
        if self._last_result is None:
            self.export_failed.emit("Aucune transcription à exporter.")
            return

        output_dir = Path(
            self._config_manager.get("export.output_directory")
        )
        extension = self._export_service.extension_for(format_name)
        output_path = output_dir / f"{base_name}{extension}"

        try:
            self._export_service.export(
                self._last_result,
                output_path,
                format_name,
            )
            self.export_succeeded.emit(str(output_path))
        except Exception as exc:
            self.export_failed.emit(str(exc))

"""Contrôleur d'orchestration du pipeline complet MeetingAI.

Ce module fournit ``PipelineController``, qui enchaîne automatiquement la
transcription, la génération du résumé IA et l'export du résultat. Chaque étape
est déléguée aux contrôleurs dédiés existants afin d'éviter toute duplication de
logique.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from meetingai.controllers.export_controller import ExportController
from meetingai.controllers.summarization_controller import (
    SummarizationController,
)
from meetingai.controllers.transcription_controller import (
    TranscriptionController,
)
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)
from meetingai.services.summarization.summary_result import SummaryResult


class PipelineController(QObject):
    """Orchestre le traitement complet d'un média.

    Le pipeline exécute successivement :

    1. transcription du média ;
    2. génération d'un résumé IA à partir de la transcription ;
    3. export de la transcription au format TXT.

    Si une étape échoue, le traitement s'arrête immédiatement et une erreur est
    propagée via ``pipeline_failed``. Le contrôleur ne redéfinit aucune logique
    métier : il se contente de connecter les signaux des contrôleurs dédiés.

    Args:
        transcription_controller: Contrôleur de transcription.
        summarization_controller: Contrôleur de résumé IA.
        export_controller: Contrôleur d'export.
        parent: QObject parent éventuel.
    """

    pipeline_started = Signal()
    pipeline_step_started = Signal(str)
    pipeline_progress = Signal(int)
    pipeline_succeeded = Signal(list)
    pipeline_failed = Signal(str)

    def __init__(
        self,
        transcription_controller: TranscriptionController,
        summarization_controller: SummarizationController,
        export_controller: ExportController,
        parent: QObject | None = None,
    ) -> None:
        """Initialise le contrôleur de pipeline."""
        super().__init__(parent)
        self._transcription_controller = transcription_controller
        self._summarization_controller = summarization_controller
        self._export_controller = export_controller
        self._active: bool = False
        self._export_paths: list[str] = []
        self._transcription_result: TranscriptionResult | None = None
        self._summary_result: SummaryResult | None = None
        self._wire_signals()

    def _wire_signals(self) -> None:
        """Connecte les signaux des contrôleurs délégués."""
        self._transcription_controller.transcription_progress.connect(
            self._on_transcription_progress
        )
        self._transcription_controller.transcription_ready.connect(
            self._on_transcription_ready
        )
        self._transcription_controller.transcription_failed.connect(
            self._on_transcription_failed
        )
        self._summarization_controller.summary_ready.connect(
            self._on_summary_ready
        )
        self._summarization_controller.summary_failed.connect(
            self._on_summary_failed
        )
        self._export_controller.export_succeeded.connect(
            self._on_export_succeeded
        )
        self._export_controller.export_failed.connect(
            self._on_export_failed
        )

    def start(self, media: MediaFile | None) -> None:
        """Démarre le pipeline complet sur le média fourni.

        Args:
            media: Média à traiter. Si ``None``, le pipeline échoue
                immédiatement.
        """
        if self._active:
            self.pipeline_failed.emit("Un pipeline est déjà en cours.")
            return
        if media is None:
            self.pipeline_failed.emit("Aucun média sélectionné.")
            return

        self._active = True
        self._export_paths = []
        self._transcription_result = None
        self._summary_result = None
        self.pipeline_started.emit()
        self._enter_step("transcription")
        self._transcription_controller.transcribe(media)

    def _enter_step(self, step: str) -> None:
        """Émet le signal d'étape en cours."""
        self.pipeline_step_started.emit(step)

    def _on_transcription_progress(self, value: int) -> None:
        """Propage la progression de la transcription."""
        if not self._active:
            return
        self.pipeline_progress.emit(value)

    def _on_transcription_ready(self, result: TranscriptionResult) -> None:
        """Passe à l'étape de résumé IA après transcription réussie."""
        if not self._active:
            return
        self._transcription_result = result
        self._enter_step("summarization")
        self._summarization_controller.on_transcription_ready(result)
        self._summarization_controller.summarize_current_transcription()

    def _on_transcription_failed(self, message: str) -> None:
        """Arrête le pipeline si la transcription échoue."""
        if not self._active:
            return
        self._finish_failed(f"Transcription échouée : {message}")

    def _on_summary_ready(self, summary: SummaryResult) -> None:
        """Passe à l'étape d'export après résumé réussi."""
        if not self._active:
            return
        self._summary_result = summary
        self._enter_step("export")
        if self._transcription_result is None:
            self._finish_failed("Aucune transcription disponible pour l'export.")
            return
        self._export_controller.on_transcription_ready(
            self._transcription_result
        )
        self._export_controller.export_txt()

    def _on_summary_failed(self, message: str) -> None:
        """Arrête le pipeline si le résumé échoue."""
        if not self._active:
            return
        self._finish_failed(f"Résumé IA échoué : {message}")

    def _on_export_succeeded(self, path: str) -> None:
        """Termine le pipeline après export réussi."""
        if not self._active:
            return
        self._export_paths.append(path)
        self._finish_succeeded()

    def _on_export_failed(self, message: str) -> None:
        """Arrête le pipeline si l'export échoue."""
        if not self._active:
            return
        self._finish_failed(f"Export échoué : {message}")

    def _finish_succeeded(self) -> None:
        """Émet le signal de succès et réinitialise l'état."""
        self._active = False
        self.pipeline_succeeded.emit(self._export_paths.copy())

    def _finish_failed(self, message: str) -> None:
        """Émet le signal d'échec et réinitialise l'état."""
        self._active = False
        self.pipeline_failed.emit(message)

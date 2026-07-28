"""Contrôleur dédié aux opérations de transcription."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from meetingai.core.task import Task, TaskStatus
from meetingai.core.task_manager import TaskManager
from meetingai.core.worker_manager import WorkerManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TranscriptionController(QObject):
    """Orchestre les transcriptions en encapsulant le service Speech-To-Text.

    Ce contrôleur est responsable de la création et du suivi de la tâche de
    transcription, de l'appel au ``SpeechToTextService`` et de l'émission des
    signaux de progression et de résultat.

    Les services restent synchrones ; l'exécution asynchrone via ``Worker`` ou
    ``QThread`` sera introduite dans une future story sans modifier l'API
    publique de ce contrôleur.

    Args:
        speech_to_text_service: Service de transcription à utiliser.
        task_manager: Gestionnaire de tâches.
        worker_manager: Gestionnaire de workers, préparé pour les futures
            exécutions asynchrones.
        logger_manager: Gestionnaire de logs.
        parent: Widget parent optionnel pour les boîtes de dialogue.
    """

    transcription_started = Signal(object)
    transcription_progress = Signal(int)
    transcription_ready = Signal(object)
    transcription_failed = Signal(str)

    def __init__(
        self,
        speech_to_text_service: SpeechToTextService,
        task_manager: TaskManager,
        worker_manager: WorkerManager,
        logger_manager: LoggerManager,
        parent: object | None = None,
    ) -> None:
        """Initialise le contrôleur de transcription."""
        super().__init__(parent)
        self._speech_to_text_service = speech_to_text_service
        self._task_manager = task_manager
        self._worker_manager = worker_manager
        self._logger = logger_manager.get_logger(__name__)
        self._parent = parent

    def transcribe(self, media: MediaFile | None) -> Task | None:
        """Lance la transcription du média fourni.

        Args:
            media: Média à transcrire. Si ``None``, un avertissement est affiché.

        Returns:
            La tâche de transcription créée, ou ``None`` si aucun média n'est
            fourni.
        """
        if media is None:
            self._logger.warning("Tentative de transcription sans média")
            QMessageBox.warning(
                self._parent,
                "Aucun média",
                "Veuillez d'abord sélectionner un média.",
            )
            return None

        task = self._task_manager.create_task("transcription")
        self.transcription_started.emit(task)
        self.transcription_progress.emit(0)

        try:
            task.status = TaskStatus.RUNNING
            result: TranscriptionResult = self._speech_to_text_service.transcribe(
                media,
                task,
            )
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            self._logger.error("Échec de la transcription : %s", exc)
            self.transcription_progress.emit(0)
            self.transcription_failed.emit(str(exc))
            return task

        task.status = TaskStatus.COMPLETED
        task.result = result
        self.transcription_progress.emit(100)
        self._logger.info("Transcription terminée : %s", result.text)
        self.transcription_ready.emit(result)
        return task

    def cancel(self, task: Task) -> None:
        """Prépare l'annulation d'une transcription.

        Args:
            task: Tâche de transcription à annuler.

        Raises:
            NotImplementedError: L'annulation sera implémentée dans une future
                story avec l'exécution asynchrone.
        """
        raise NotImplementedError(
            "L'annulation de transcription n'est pas encore supportée."
        )

"""Contrôleur dédié aux opérations de transcription."""

from __future__ import annotations

import uuid

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from meetingai.core.task import Task, TaskStatus
from meetingai.core.task_manager import TaskManager
from meetingai.core.transcription_worker import TranscriptionWorker
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
    """Orchestre les transcriptions de manière asynchrone.

    Ce contrôleur est responsable de la création et du suivi de la tâche de
    transcription. Il délègue l'exécution à un ``TranscriptionWorker`` tournant
    dans un ``QThread`` afin de ne pas bloquer l'interface graphique.

    ``SpeechToTextService`` reste strictement synchrone : l'asynchronisme est
    uniquement une préoccupation du contrôleur et du worker.

    Args:
        speech_to_text_service: Service de transcription à utiliser.
        task_manager: Gestionnaire de tâches.
        worker_manager: Gestionnaire de workers.
        logger_manager: Gestionnaire de logs.
        parent: Widget parent optionnel pour les boîtes de dialogue.
    """

    transcription_started = Signal(object)
    transcription_progress = Signal(int)
    transcription_ready = Signal(object)
    transcription_failed = Signal(str)
    transcription_cancelled = Signal(object)

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
        self._active_workers: dict[uuid.UUID, TranscriptionWorker] = {}

    def transcribe(self, media: MediaFile | None) -> Task | None:
        """Lance la transcription du média fourni de façon asynchrone.

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
        task.status = TaskStatus.PENDING
        self.transcription_started.emit(task)
        self.transcription_progress.emit(0)

        worker = TranscriptionWorker(
            task=task,
            speech_to_text_service=self._speech_to_text_service,
            media=media,
        )

        self._wire_worker_signals(worker, task)
        self._active_workers[task.id] = worker
        self._worker_manager.register(worker)

        worker.start()
        return task

    def _wire_worker_signals(
        self,
        worker: TranscriptionWorker,
        task: Task,
    ) -> None:
        """Connecte les signaux du worker au contrôleur."""
        worker.started.connect(
            lambda: self._logger.info("Transcription démarrée : %s", task.id)
        )
        worker.progress.connect(self.transcription_progress.emit)
        worker.finished.connect(
            lambda result: self._on_worker_finished(worker, task, result)
        )
        worker.failed.connect(
            lambda exc: self._on_worker_failed(worker, task, exc)
        )
        worker.cancelled.connect(
            lambda: self._on_worker_cancelled(worker, task)
        )

    def _on_worker_finished(
        self,
        worker: TranscriptionWorker,
        task: Task,
        result: TranscriptionResult,
    ) -> None:
        """Gère la fin réussie d'une transcription."""
        self._logger.info("Transcription terminée : %s", result.text)
        self._cleanup_worker(worker, task)
        self.transcription_progress.emit(100)
        self.transcription_ready.emit(result)

    def _on_worker_failed(
        self,
        worker: TranscriptionWorker,
        task: Task,
        exc: Exception,
    ) -> None:
        """Gère l'échec d'une transcription."""
        self._logger.error("Échec de la transcription : %s", exc)
        self._cleanup_worker(worker, task)
        self.transcription_failed.emit(str(exc))

    def _on_worker_cancelled(
        self,
        worker: TranscriptionWorker,
        task: Task,
    ) -> None:
        """Gère l'annulation d'une transcription."""
        self._logger.info("Transcription annulée : %s", task.id)
        self._cleanup_worker(worker, task)
        self.transcription_cancelled.emit(task)

    def _cleanup_worker(
        self,
        worker: TranscriptionWorker,
        task: Task,
    ) -> None:
        """Supprime le worker du registre actif et du WorkerManager."""
        self._active_workers.pop(task.id, None)
        try:
            self._worker_manager.unregister(worker.task.id)
        except KeyError:
            pass

    def cancel(self, task: Task) -> None:
        """Demande l'annulation d'une transcription en cours.

        Args:
            task: Tâche de transcription à annuler.
        """
        worker = self._active_workers.get(task.id)
        if worker is not None:
            worker.cancel()
            self._logger.info(
                "Demande d'annulation de la transcription : %s", task.id
            )
        else:
            self._logger.warning("Aucun worker actif pour la tâche : %s", task.id)

"""Worker d'exécution asynchrone d'une transcription."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from meetingai.core.task import Task, TaskStatus
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class _TranscriptionThread(QThread):
    """Thread d'exécution dédié à une transcription.

    Ce thread est volontairement séparé du worker afin de conserver
    ``TranscriptionWorker`` comme simple QObject porteur de signaux, sans
    hériter de ``QThread`` et sans utiliser ``moveToThread``.
    """

    def __init__(self, worker: "TranscriptionWorker") -> None:
        """Initialise le thread avec son worker."""
        super().__init__()
        self._worker = worker

    def run(self) -> None:
        """Exécute la charge utile du worker dans le thread secondaire."""
        self._worker.run()


class TranscriptionWorker(QObject):
    """Encapsule l'exécution d'une transcription dans un thread dédié.

    Ce worker est conçu pour être exécuté via ``_TranscriptionThread``. Il
    reste un objet synchrone qui appelle ``SpeechToTextService.transcribe`` et
    émet des signaux pour communiquer avec le thread principal.

    Args:
        task: Tâche de transcription à mettre à jour.
        speech_to_text_service: Service de transcription à utiliser.
        media: Média à transcrire.
        parent: Parent Qt optionnel.
    """

    started = Signal()
    progress = Signal(int)
    finished = Signal(TranscriptionResult)
    failed = Signal(Exception)
    cancelled = Signal()

    def __init__(
        self,
        task: Task,
        speech_to_text_service: SpeechToTextService,
        media: MediaFile,
        parent: object | None = None,
    ) -> None:
        """Initialise le worker de transcription."""
        super().__init__(parent)
        self._task = task
        self._service = speech_to_text_service
        self._media = media
        self._is_cancelled = False
        self._thread: _TranscriptionThread | None = None

    @property
    def task(self) -> Task:
        """Retourne la tâche associée au worker."""
        return self._task

    def cancel(self) -> None:
        """Demande l'annulation du traitement.

        L'annulation est un point d'extension : elle permettra de court-circuiter
        le résultat ou d'interrompre un traitement futur sans modifier l'API
        publique.
        """
        self._is_cancelled = True

    def start(self) -> None:
        """Démarre le thread d'exécution et connecte son cycle de vie."""
        self._thread = _TranscriptionThread(self)
        self.finished.connect(lambda _result: self._thread.quit())
        self.failed.connect(lambda _exc: self._thread.quit())
        self.cancelled.connect(self._thread.quit)
        self._thread.finished.connect(self.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def run(self) -> None:
        """Exécute la transcription et émet les signaux de progression.

        Cette méthode est appelée depuis le thread secondaire.
        """
        self.started.emit()

        if self._is_cancelled:
            self._task.status = TaskStatus.CANCELLED
            self.cancelled.emit()
            return

        self.progress.emit(0)
        try:
            self._task.status = TaskStatus.RUNNING

            def _progress_callback(value: int) -> None:
                self.progress.emit(value)
                self._task.update_progress(value)

            result: TranscriptionResult = self._service.transcribe(
                self._media,
                self._task,
                progress_callback=_progress_callback,
            )
            if self._is_cancelled:
                self._task.status = TaskStatus.CANCELLED
                self.cancelled.emit()
                return

            self._task.status = TaskStatus.COMPLETED
            self._task.result = result
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as exc:
            self._task.status = TaskStatus.FAILED
            self._task.error = str(exc)
            self.failed.emit(exc)

"""Implémentation fictive de SpeechToTextService pour valider le flux."""

import uuid
from collections.abc import Callable

from meetingai.core.task import Task
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class FakeSpeechToTextService(SpeechToTextService):
    """Moteur de transcription simulé.

    Cette implémentation respecte le contrat ``SpeechToTextService`` sans
    dépendre d'une bibliothèque IA. Elle retourne un texte fixe afin de valider
    l'ensemble du pipeline utilisateur.

    Elle sera remplacée ultérieurement par une implémentation réelle telle que
    ``FasterWhisperSpeechToTextService`` sans modifier la GUI.
    """

    _FIXED_TEXT: str = "Cette transcription est simulée."
    _LANGUAGE: str = "fr"
    _MODEL: str = "fake"
    _VERSION: str = "1.0.0"

    def transcribe(
        self,
        media: MediaFile,
        task: Task,
        progress_callback: Callable[[int], None] | None = None,
    ) -> TranscriptionResult:
        """Retourne un résultat de transcription fictif.

        Args:
            media: Média à transcrire.
            task: Tâche associée.
            progress_callback: Fonction optionnelle appelée avec l'avancement.

        Returns:
            Résultat de transcription simulé.
        """
        if progress_callback is not None:
            progress_callback(100)
        return TranscriptionResult(
            text=self._FIXED_TEXT,
            language=self._LANGUAGE,
            duration=0.0,
            model=self._MODEL,
            processing_time=0.0,
            metadata={},
        )

    def cancel(self, task_id: uuid.UUID) -> None:
        """Lève NotImplementedError car le service fictif ne peut pas annuler."""
        raise NotImplementedError(
            "Le service de transcription simulé ne supporte pas l'annulation."
        )

    def is_available(self) -> bool:
        """Le service fictif est toujours disponible."""
        return True

    def name(self) -> str:
        """Retourne le nom du moteur fictif."""
        return "FakeSpeechToText"

    def version(self) -> str:
        """Retourne la version du moteur fictif."""
        return self._VERSION

    def supported_languages(self) -> list[str]:
        """Retourne les langues supportées par le moteur fictif."""
        return [self._LANGUAGE]

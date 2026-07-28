"""Contrat commun des moteurs Speech-To-Text."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

from meetingai.core.task import Task
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class SpeechToTextService(ABC):
    """Interface commune pour tous les moteurs de transcription.

    Cette classe abstraite définit le contrat minimal que doit respecter
    chaque moteur Speech-To-Text intégré à MeetingAI. Elle permet de changer
    de moteur sans impacter la couche graphique ou les contrôleurs.
    """

    @abstractmethod
    def transcribe(self, media: MediaFile, task: Task) -> TranscriptionResult:
        """Lance la transcription d'un média.

        Args:
            media: Média à transcrire.
            task: Tâche associée permettant de suivre la progression.

        Returns:
            Résultat de la transcription.
        """

    @abstractmethod
    def cancel(self, task_id: uuid.UUID) -> None:
        """Annule une transcription en cours.

        Args:
            task_id: Identifiant de la tâche à annuler.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Indique si le moteur est utilisable sur ce système."""

    @abstractmethod
    def name(self) -> str:
        """Retourne le nom du moteur."""

    @abstractmethod
    def version(self) -> str:
        """Retourne la version du moteur."""

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Retourne la liste des langues supportées."""


class NullSpeechToTextService(SpeechToTextService):
    """Implémentation placeholder du moteur Speech-To-Text.

    Cette classe respecte le contrat ``SpeechToTextService`` sans réaliser
    aucune transcription. Elle permet à l'application de démarrer sans moteur
    IA réel et sera remplacée par une implémentation concrète lors de la
    configuration de l'utilisateur.
    """

    def transcribe(self, media: MediaFile, task: Task) -> TranscriptionResult:
        """Lève NotImplementedError car aucun moteur n'est installé."""
        raise NotImplementedError(
            "Aucun moteur Speech-To-Text n'est configuré."
        )

    def cancel(self, task_id: uuid.UUID) -> None:
        """Lève NotImplementedError car aucun moteur n'est installé."""
        raise NotImplementedError(
            "Aucun moteur Speech-To-Text n'est configuré."
        )

    def is_available(self) -> bool:
        """Le moteur placeholder n'est jamais disponible."""
        return False

    def name(self) -> str:
        """Retourne le nom du moteur placeholder."""
        return "NullSpeechToText"

    def version(self) -> str:
        """Retourne une version par défaut."""
        return "0.0.0"

    def supported_languages(self) -> list[str]:
        """Retourne une liste vide."""
        return []

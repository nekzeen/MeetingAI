"""Contrôleur dédié au résumé IA des transcriptions."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from meetingai.config.config_manager import ConfigManager
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)
from meetingai.services.summarization.summary_profile import ProfileRegistry
from meetingai.services.summarization.summary_result import SummaryResult
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)


class SummarizationController(QObject):
    """Orchestre la génération d'un résumé IA à partir d'une transcription.

    Le contrôleur garde en mémoire la dernière transcription prête et déclenche
    le résumé via le provider configuré lorsque l'utilisateur demande l'action.
    Il reste indépendant du provider grâce à ``SummarizationFactory``.

    Args:
        factory: Factory des providers de résumé IA.
        config_manager: Gestionnaire de configuration pour la sélection du provider.
        parent: QObject parent éventuel.
    """

    summary_ready = Signal(SummaryResult)
    summary_failed = Signal(str)

    def __init__(
        self,
        factory: SummarizationFactory,
        config_manager: ConfigManager,
        parent: QObject | None = None,
    ) -> None:
        """Initialise le contrôleur de résumé IA."""
        super().__init__(parent)
        self._factory = factory
        self._config = config_manager
        self._last_transcription: TranscriptionResult | None = None

    def on_transcription_ready(self, result: TranscriptionResult) -> None:
        """Conserve la dernière transcription disponible.

        Args:
            result: Résultat de transcription à résumer ultérieurement.
        """
        self._last_transcription = result

    def _resolve_profile(self, profile_key: str) -> SummaryProfile:
        """Retourne le profil de résumé correspondant à la clé.

        Args:
            profile_key: Clé du profil souhaité.

        Returns:
            Instance de ``SummaryProfile``.
        """
        if profile_key == ProfileRegistry.build_custom_profile().key:
            custom_instruction = self._config.get(
                "summarization.custom_profile_instruction"
            )
            return ProfileRegistry.build_custom_profile(custom_instruction)
        return ProfileRegistry().get(profile_key)

    def summarize_current_transcription(self) -> None:
        """Résume la dernière transcription disponible.

        Émet ``summary_ready`` avec le résultat ou ``summary_failed`` en cas
        d'erreur.
        """
        if self._last_transcription is None:
            self.summary_failed.emit("Aucune transcription à résumer.")
            return

        provider_name = self._config.get("summarization.provider") or "fake"
        profile_key = self._config.get("summarization.profile") or "concise"
        try:
            service = self._factory.create(provider_name, config=self._config)
            profile = self._resolve_profile(profile_key)
            summary = service.summarize(self._last_transcription.text, profile)
            self.summary_ready.emit(summary)
        except Exception as exc:
            self.summary_failed.emit(str(exc))

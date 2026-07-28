"""Factory de création des moteurs Speech-To-Text."""

from __future__ import annotations

from typing import Callable

from meetingai.config.speech_to_text_configuration import (
    SpeechToTextConfiguration,
)
from meetingai.services.speech_to_text.fake_speech_to_text_service import (
    FakeSpeechToTextService,
)
from meetingai.services.speech_to_text.faster_whisper_service import (
    FasterWhisperService,
)
from meetingai.services.speech_to_text.speech_to_text_service import (
    SpeechToTextService,
)


class SpeechToTextFactory:
    """Construit une instance de ``SpeechToTextService`` selon la configuration.

    La factory enregistre les providers disponibles dans un registre. L'ajout
    d'un nouveau moteur se fait par ``register_provider`` sans modifier le
    code existant, respectant ainsi le principe Open/Closed.
    """

    def __init__(self) -> None:
        """Initialise le registre avec les providers par défaut."""
        self._providers: dict[
            str,
            Callable[[SpeechToTextConfiguration], SpeechToTextService],
        ] = {}
        self.register_provider("fake", self._build_fake)
        self.register_provider("faster-whisper", self._build_faster_whisper)

    def register_provider(
        self,
        name: str,
        builder: Callable[[SpeechToTextConfiguration], SpeechToTextService],
    ) -> None:
        """Enregistre un nouveau provider.

        Args:
            name: Identifiant du provider.
            builder: Fonction créant le service à partir de la configuration.
        """
        self._providers[name] = builder

    def create(self, config: SpeechToTextConfiguration) -> SpeechToTextService:
        """Instancie le service correspondant à la configuration.

        Args:
            config: Configuration Speech-To-Text.

        Returns:
            Instance de ``SpeechToTextService``.

        Raises:
            ValueError: Si le provider n'est pas enregistré.
        """
        builder = self._providers.get(config.provider)
        if builder is None:
            raise ValueError(
                f"Provider Speech-To-Text inconnu : {config.provider}"
            )
        return builder(config)

    @staticmethod
    def _build_fake(_config: SpeechToTextConfiguration) -> SpeechToTextService:
        """Construit le service fictif."""
        return FakeSpeechToTextService()

    @staticmethod
    def _build_faster_whisper(
        config: SpeechToTextConfiguration,
    ) -> SpeechToTextService:
        """Construit le service faster-whisper."""
        return FasterWhisperService(
            model_size=config.model_name,
            device=config.device,
            compute_type=config.compute_type,
        )

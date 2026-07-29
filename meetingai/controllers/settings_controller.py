"""Contrôleur dédié à la gestion des paramètres de l'application."""

from __future__ import annotations

from meetingai.config.config_manager import ConfigManager
from meetingai.services.speech_to_text.speech_to_text_factory import (
    SpeechToTextFactory,
)
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)


class SettingsController:
    """Charge et sauvegarde les paramètres utilisateur.

    Ce contrôleur est responsable de la lecture et de la persistance de la
    configuration via ``ConfigManager``. Il interroge les factories de
    providers pour alimenter les listes de sélection sans valeurs codées en
    dur. Il ne contient aucune logique d'interface graphique.

    Args:
        config_manager: Gestionnaire de configuration de l'application.
        speech_to_text_factory: Factory des providers Speech-To-Text.
        summarization_factory: Factory des providers de résumé IA.
    """

    _THEMES: tuple[str, ...] = ("light", "dark")
    _LANGUAGES: tuple[str, ...] = ("fr", "en")
    _DEVICES: tuple[str, ...] = ("auto", "cpu", "cuda")
    _COMPUTE_TYPES: tuple[str, ...] = ("int8", "float16", "int16", "float32")

    def __init__(
        self,
        config_manager: ConfigManager,
        speech_to_text_factory: SpeechToTextFactory,
        summarization_factory: SummarizationFactory,
    ) -> None:
        """Initialise le contrôleur avec ses dépendances."""
        self._config = config_manager
        self._speech_to_text_factory = speech_to_text_factory
        self._summarization_factory = summarization_factory

    def load_settings(self) -> dict[str, str]:
        """Charge les paramètres actuels de l'application.

        Returns:
            Dictionnaire des paramètres affichés dans la fenêtre.
        """
        return {
            "theme": self._config.get("application.theme"),
            "language": self._config.get("application.language"),
            "provider": self._config.get("speech_to_text.provider"),
            "speech_to_text_providers": self.available_speech_to_text_providers(),
            "model_name": self._config.get("speech_to_text.model_name"),
            "device": self._config.get("speech_to_text.device"),
            "compute_type": self._config.get("speech_to_text.compute_type"),
            "output_directory": self._config.get("export.output_directory"),
            "summarization_provider": self._config.get(
                "summarization.provider"
            ),
            "summarization_providers": self.available_summarization_providers(),
        }

    def save_settings(self, settings: dict[str, str]) -> None:
        """Sauvegarde les paramètres modifiés dans la configuration.

        Args:
            settings: Dictionnaire des paramètres à persister.

        Raises:
            ValueError: Si un paramètre n'est pas supporté.
        """
        self._validate(settings)

        self._config.set("application.theme", settings["theme"])
        self._config.set("application.language", settings["language"])
        self._config.set("speech_to_text.provider", settings["provider"])
        self._config.set("speech_to_text.model_name", settings["model_name"])
        self._config.set("speech_to_text.device", settings["device"])
        self._config.set("speech_to_text.compute_type", settings["compute_type"])
        self._config.set(
            "export.output_directory", settings["output_directory"]
        )
        self._config.set(
            "summarization.provider", settings["summarization_provider"]
        )
        self._config.save()

    def _validate(self, settings: dict[str, str]) -> None:
        """Vérifie que les valeurs fournies sont supportées."""
        if settings["theme"] not in self._THEMES:
            raise ValueError(f"Thème non supporté : {settings['theme']}")
        if settings["language"] not in self._LANGUAGES:
            raise ValueError(f"Langue non supportée : {settings['language']}")
        if settings["provider"] not in self.available_speech_to_text_providers():
            raise ValueError(f"Provider non supporté : {settings['provider']}")
        if settings["device"] not in self._DEVICES:
            raise ValueError(f"Périphérique non supporté : {settings['device']}")
        if settings["compute_type"] not in self._COMPUTE_TYPES:
            raise ValueError(
                f"Type de calcul non supporté : {settings['compute_type']}"
            )
        if (
            settings["summarization_provider"]
            not in self.available_summarization_providers()
        ):
            raise ValueError(
                "Provider de résumé non supporté : "
                f"{settings['summarization_provider']}"
            )

    def available_themes(self) -> list[str]:
        """Retourne la liste des thèmes disponibles."""
        return list(self._THEMES)

    def available_languages(self) -> list[str]:
        """Retourne la liste des langues disponibles."""
        return list(self._LANGUAGES)

    def available_speech_to_text_providers(self) -> list[str]:
        """Retourne la liste des providers Speech-To-Text disponibles."""
        return self._speech_to_text_factory.available_providers()

    def available_summarization_providers(self) -> list[str]:
        """Retourne la liste des providers de résumé IA disponibles."""
        return self._summarization_factory.available_providers()

    def available_devices(self) -> list[str]:
        """Retourne la liste des périphériques d'exécution disponibles."""
        return list(self._DEVICES)

    def available_compute_types(self) -> list[str]:
        """Retourne la liste des types de calcul disponibles."""
        return list(self._COMPUTE_TYPES)

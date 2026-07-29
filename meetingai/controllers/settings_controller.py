"""Contrôleur dédié à la gestion des paramètres de l'application."""

from __future__ import annotations

from meetingai.config.config_manager import ConfigManager


class SettingsController:
    """Charge et sauvegarde les paramètres utilisateur.

    Ce contrôleur est responsable de la lecture et de la persistance de la
    configuration via ``ConfigManager``. Il ne contient aucune logique
    d'interface graphique.

    Args:
        config_manager: Gestionnaire de configuration de l'application.
    """

    _THEMES: tuple[str, ...] = ("light", "dark")
    _LANGUAGES: tuple[str, ...] = ("fr", "en")
    _PROVIDERS: tuple[str, ...] = ("fake", "faster-whisper")
    _DEVICES: tuple[str, ...] = ("auto", "cpu", "cuda")
    _COMPUTE_TYPES: tuple[str, ...] = ("int8", "float16", "int16", "float32")

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialise le contrôleur avec le gestionnaire de configuration."""
        self._config = config_manager

    def load_settings(self) -> dict[str, str]:
        """Charge les paramètres actuels de l'application.

        Returns:
            Dictionnaire des paramètres affichés dans la fenêtre.
        """
        return {
            "theme": self._config.get("application.theme"),
            "language": self._config.get("application.language"),
            "provider": self._config.get("speech_to_text.provider"),
            "model_name": self._config.get("speech_to_text.model_name"),
            "device": self._config.get("speech_to_text.device"),
            "compute_type": self._config.get("speech_to_text.compute_type"),
            "output_directory": self._config.get("export.output_directory"),
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
        self._config.save()

    def _validate(self, settings: dict[str, str]) -> None:
        """Vérifie que les valeurs fournies sont supportées."""
        if settings["theme"] not in self._THEMES:
            raise ValueError(f"Thème non supporté : {settings['theme']}")
        if settings["language"] not in self._LANGUAGES:
            raise ValueError(f"Langue non supportée : {settings['language']}")
        if settings["provider"] not in self._PROVIDERS:
            raise ValueError(f"Provider non supporté : {settings['provider']}")
        if settings["device"] not in self._DEVICES:
            raise ValueError(f"Périphérique non supporté : {settings['device']}")
        if settings["compute_type"] not in self._COMPUTE_TYPES:
            raise ValueError(
                f"Type de calcul non supporté : {settings['compute_type']}"
            )

    def available_themes(self) -> list[str]:
        """Retourne la liste des thèmes disponibles."""
        return list(self._THEMES)

    def available_languages(self) -> list[str]:
        """Retourne la liste des langues disponibles."""
        return list(self._LANGUAGES)

    def available_providers(self) -> list[str]:
        """Retourne la liste des providers Speech-To-Text disponibles."""
        return list(self._PROVIDERS)

    def available_devices(self) -> list[str]:
        """Retourne la liste des périphériques d'exécution disponibles."""
        return list(self._DEVICES)

    def available_compute_types(self) -> list[str]:
        """Retourne la liste des types de calcul disponibles."""
        return list(self._COMPUTE_TYPES)

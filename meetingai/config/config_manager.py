"""Gestionnaire de configuration persistante pour MeetingAI.

Ce module fournit une classe unique, `ConfigManager`, capable de charger,
modifier et sauvegarder la configuration de l'application au format JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from meetingai.config.speech_to_text_configuration import (
    SpeechToTextConfiguration,
)


@dataclass
class ApplicationConfig:
    """Paramètres généraux de l'application."""

    theme: str = "light"
    language: str = "fr"


@dataclass
class TranscriptionConfig:
    """Paramètres de transcription."""

    model: str = "small"
    device: str = "cpu"


@dataclass
class ExportConfig:
    """Paramètres d'export."""

    output_directory: str = "output"


@dataclass
class LoggingConfig:
    """Paramètres de journalisation."""

    level: str = "INFO"


@dataclass
class SummarizationConfig:
    """Paramètres de résumé IA."""

    provider: str = "fake"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout: int = 30


@dataclass
class ConfigManager:
    """Gère le chargement et la persistance de la configuration.

    La configuration est stockée dans un fichier JSON. Si le fichier est
    absent au chargement, il est automatiquement créé avec les valeurs par
    défaut.

    Attributes:
        config_path: Chemin du fichier de configuration JSON.
    """

    config_path: Path
    _config: dict[str, Any] = field(init=False, repr=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Normalise le chemin et charge la configuration."""
        self.config_path = Path(self.config_path)
        self._config = self._default_config()
        self.load()

    @staticmethod
    def _default_config() -> dict[str, Any]:
        """Retourne la configuration par défaut sous forme de dictionnaire.

        Returns:
            Dictionnaire des valeurs par défaut, regroupées par section.
        """
        return {
            "application": asdict(ApplicationConfig()),
            "transcription": asdict(TranscriptionConfig()),
            "speech_to_text": asdict(SpeechToTextConfiguration()),
            "export": asdict(ExportConfig()),
            "logging": asdict(LoggingConfig()),
            "summarization": asdict(SummarizationConfig()),
        }

    def load(self) -> None:
        """Charge la configuration depuis le fichier JSON.

        Si le fichier n'existe pas, il est créé avec les valeurs par défaut.
        Les clés manquantes dans le fichier sont complétées par les valeurs
        par défaut afin de garantir la compatibilité ascendante.
        """
        if not self.config_path.exists():
            self.save()
            return

        with self.config_path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)

        if not isinstance(loaded, dict):
            loaded = {}

        self._config = self._merge_with_defaults(loaded)
        self.save()

    def _merge_with_defaults(self, loaded: dict[str, Any]) -> dict[str, Any]:
        """Fusionne la configuration chargée avec les valeurs par défaut.

        Args:
            loaded: Configuration lue depuis le fichier JSON.

        Returns:
            Configuration complète avec toutes les clés par défaut présentes.
        """
        defaults = self._default_config()
        merged: dict[str, Any] = {}

        for section, default_values in defaults.items():
            loaded_section = loaded.get(section, {})
            if not isinstance(loaded_section, dict):
                loaded_section = {}
            merged[section] = {
                key: loaded_section.get(key, default_value)
                for key, default_value in default_values.items()
            }

        return merged

    def save(self) -> None:
        """Sauvegarde la configuration actuelle dans le fichier JSON.

        Les répertoires parents sont créés automatiquement si nécessaire.
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self._config, file, indent=4, ensure_ascii=False)
            file.write("\n")

    def get(self, key: str) -> Any:
        """Retourne la valeur associée à une clé en notation pointée.

        Args:
            key: Clé de la forme ``section.parametre``.

        Returns:
            Valeur du paramètre demandé.

        Raises:
            KeyError: Si la clé ou la section n'existe pas.
        """
        parts = key.split(".")
        value: Any = self._config

        for part in parts:
            if not isinstance(value, dict):
                raise KeyError(f"Clé invalide : {key}")
            value = value[part]

        return value

    def set(self, key: str, value: Any) -> None:
        """Modifie la valeur d'une clé en notation pointée.

        Args:
            key: Clé de la forme ``section.parametre``.
            value: Nouvelle valeur à affecter.

        Raises:
            KeyError: Si la section ou le chemin intermédiaire n'existe pas.
        """
        parts = key.split(".")
        target: Any = self._config

        for part in parts[:-1]:
            if not isinstance(target, dict) or part not in target:
                raise KeyError(f"Section inconnue : {part}")
            target = target[part]

        target[parts[-1]] = value

    @property
    def speech_to_text(self) -> SpeechToTextConfiguration:
        """Retourne la configuration Speech-To-Text typée.

        Returns:
            Instance ``SpeechToTextConfiguration`` extraite de la configuration.
        """
        return SpeechToTextConfiguration(**self._config["speech_to_text"])

    def reset_to_defaults(self) -> None:
        """Réinitialise la configuration aux valeurs par défaut."""
        self._config = self._default_config()
        self.save()

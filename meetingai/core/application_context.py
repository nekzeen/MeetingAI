"""Composition racine de l'application MeetingAI.

Ce module regroupe l'instanciation des composants centraux de l'application :
configuration, journalisation, registre de services et gestionnaire d'actions.
Il constitue le point d'entrée unique de l'injection de dépendances.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from meetingai.config.config_manager import ConfigManager
from meetingai.core.service_registry import ServiceRegistry
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager


class ApplicationContext:
    """Conteneur racine des composants partagés de MeetingAI.

    Cette classe crée et expose les instances uniques de ``ConfigManager``,
    ``LoggerManager``, ``ServiceRegistry`` et ``ActionManager``. Elle
    enregistre automatiquement ces composants dans le ``ServiceRegistry``
    afin de préparer l'injection de dépendances futures.

    Args:
        config_path: Chemin du fichier de configuration JSON. Par défaut,
            ``config/config.json``.
        logs_dir: Répertoire des fichiers de journalisation. Par défaut,
            le dossier ``logs`` à la racine du projet.
    """

    def __init__(
        self,
        config_path: str | Path = "config/config.json",
        logs_dir: str | Path = "logs",
    ) -> None:
        """Initialise les composants centraux de l'application."""
        self.config: ConfigManager = ConfigManager(config_path=config_path)
        self.logger: LoggerManager = LoggerManager(
            config_manager=self.config, logs_dir=logs_dir
        )
        self.service_registry: ServiceRegistry = ServiceRegistry()
        self.action_manager: ActionManager = ActionManager()
        self._register_components()

    def _register_components(self) -> None:
        """Enregistre les composants partagés dans le registre de services."""
        self.service_registry.register("config_manager", self.config)
        self.service_registry.register("logger_manager", self.logger)
        self.service_registry.register("action_manager", self.action_manager)

    def get_service(self, name: str) -> Any:
        """Retourne un service enregistré dans le registre.

        Args:
            name: Clé du service demandé.

        Returns:
            Instance du service enregistrée.

        Raises:
            KeyError: Si le service n'est pas enregistré.
        """
        return self.service_registry.get(name)

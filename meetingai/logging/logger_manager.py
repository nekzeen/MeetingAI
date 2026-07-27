"""Gestionnaire centralisé des logs pour MeetingAI.

Ce module fournit un singleton, ``LoggerManager``, qui configure un logger
principal nommé ``meetingai``. Tous les modules de l'application peuvent
obtenir un logger via cette classe pour garantir un format et une gestion des
fichiers uniformes.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import ClassVar

from meetingai.config.config_manager import ConfigManager


class LoggerManager:
    """Configure et fournit l'accès au logger partagé de MeetingAI.

    Cette classe implémente le pattern singleton afin d'éviter les
    initialisations multiples du système de log. Elle utilise un
    ``RotatingFileHandler`` pour limiter la taille des fichiers de log et un
    ``StreamHandler`` pour la sortie console.

    Attributes:
        config_manager: Instance de ``ConfigManager`` utilisée pour lire le
            niveau de log (``logging.level``).
        logs_dir: Répertoire contenant les fichiers de log. Par défaut, le
            dossier ``logs`` à la racine du projet.
    """

    _instance: ClassVar[LoggerManager | None] = None
    _initialized: ClassVar[bool] = False

    def __new__(
        cls,
        config_manager: ConfigManager | None = None,
        logs_dir: Path | str | None = None,
    ) -> LoggerManager:
        """Retourne l'instance unique du gestionnaire de logs."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        logs_dir: Path | str | None = None,
    ) -> None:
        """Initialise le gestionnaire de logs.

        L'initialisation effective n'a lieu qu'une seule fois. Les appels
        suivants mettent éventuellement à jour la configuration si un nouveau
        ``ConfigManager`` est fourni.

        Args:
            config_manager: Gestionnaire de configuration. Si ``None``, le
                niveau par défaut ``INFO`` est utilisé.
            logs_dir: Chemin du répertoire de log. Par défaut ``logs`` dans
                le répertoire de travail courant.
        """
        if config_manager is not None:
            self._config_manager = config_manager
        if logs_dir is not None:
            self._logs_dir = Path(logs_dir)

        if LoggerManager._initialized:
            return

        LoggerManager._initialized = True
        self._config_manager = config_manager
        self._logs_dir = Path(logs_dir) if logs_dir else Path("logs").resolve()
        self._log_format = (
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        self._logger = logging.getLogger("meetingai")
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure les gestionnaires de log."""
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)
        self._logger.setLevel(self._resolve_level())
        self._logger.propagate = False

        formatter = logging.Formatter(self._log_format)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        try:
            self._logs_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                self._logs_dir / "meetingai.log",
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
        except OSError:
            # Si le fichier de log est inaccessible, on conserve au moins la
            # sortie console pour ne jamais bloquer l'application.
            pass

    def _resolve_level(self) -> int:
        """Détermine le niveau de log depuis la configuration.

        Returns:
            Niveau de log compatible avec le module ``logging``.
        """
        if self._config_manager is None:
            return logging.INFO

        try:
            level_name = self._config_manager.get("logging.level")
        except KeyError:
            return logging.INFO

        if not isinstance(level_name, str):
            return logging.INFO

        level = logging.getLevelName(level_name.upper())
        return level if isinstance(level, int) else logging.INFO

    def get_logger(self, name: str) -> logging.Logger:
        """Retourne un logger enfant du logger principal.

        Args:
            name: Nom du module demandant le logger. Il est recommandé
                d'utiliser ``__name__``.

        Returns:
            Logger configuré avec les gestionnaires partagés.
        """
        return self._logger.getChild(name)

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise l'instance singleton. Réservé aux tests."""
        if cls._instance is not None:
            logger = cls._instance._logger
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            cls._instance = None
        cls._initialized = False

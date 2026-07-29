"""Gestionnaire centralisé des QAction de MeetingAI."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget

from meetingai.controllers.media_controller import MediaController


class ActionManager:
    """Crée et expose les QAction partagées de l'application.

    Cette classe suit le pattern singleton afin de garantir une unique source
    de vérité pour les actions réutilisées par les menus, les barres d'outils,
    les raccourcis clavier et les menus contextuels.

    Aucune logique métier n'est rattachée aux actions ici.

    Args:
        parent: Widget parent utilisé pour les QAction.
    """

    _instance: ClassVar[ActionManager | None] = None
    _initialized: ClassVar[bool] = False

    def __new__(cls, parent: QWidget | None = None) -> ActionManager:
        """Retourne l'instance unique du gestionnaire d'actions."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise les actions si l'instance n'a pas encore été créée."""
        if ActionManager._initialized:
            return
        ActionManager._initialized = True
        self._parent = parent
        self._create_actions()

    def _create_actions(self) -> None:
        """Instancie les QAction de base de l'application."""
        self.new_action = QAction("Nouveau", self._parent)
        self.open_action = QAction("Ouvrir", self._parent)
        self.save_action = QAction("Enregistrer", self._parent)
        self.export_txt_action = QAction("Exporter en TXT", self._parent)
        self.export_markdown_action = QAction("Exporter en Markdown", self._parent)
        self.quit_action = QAction("Quitter", self._parent)
        self.transcribe_action = QAction("Transcrire", self._parent)
        self.summarize_action = QAction("Résumer la transcription", self._parent)
        self.preferences_action = QAction("Préférences", self._parent)
        self.about_action = QAction("À propos", self._parent)

    @property
    def actions(self) -> dict[str, QAction]:
        """Retourne un dictionnaire nommé des actions disponibles.

        Returns:
            Dictionnaire clé/valeur des QAction de l'application.
        """
        return {
            "new": self.new_action,
            "open": self.open_action,
            "save": self.save_action,
            "export_txt": self.export_txt_action,
            "export_markdown": self.export_markdown_action,
            "quit": self.quit_action,
            "transcribe": self.transcribe_action,
            "summarize": self.summarize_action,
            "preferences": self.preferences_action,
            "about": self.about_action,
        }

    def connect_open_media(self, controller: MediaController) -> None:
        """Connecte l'action ``Ouvrir`` au contrôleur média.

        Args:
            controller: Contrôleur chargé de la sélection et de l'ouverture
                d'un fichier média.
        """
        self.open_action.triggered.connect(controller.open_media)

    def connect_transcribe(self, slot: Callable[[], None]) -> None:
        """Connecte l'action ``Transcrire`` au slot fourni.

        Args:
            slot: Fonction sans argument appelée lors du déclenchement de
                l'action.
        """
        self.transcribe_action.triggered.connect(slot)

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise le singleton. Réservé aux tests."""
        cls._instance = None
        cls._initialized = False

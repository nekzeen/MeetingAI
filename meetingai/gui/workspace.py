"""Conteneur principal des vues de l'application MeetingAI."""

from PySide6.QtWidgets import QHBoxLayout, QWidget


class Workspace(QWidget):
    """Widget central contenant le layout principal de l'application.

    Le ``Workspace`` est un conteneur vide prévu pour accueillir les futures
    vues de l'application. Il utilise un ``QHBoxLayout`` horizontal afin de
    faciliter l'ajout de plusieurs panneaux côte à côte.

    Aucun widget métier, aucun bouton et aucune logique ne sont définis dans
    ce composant.
    """

    _MARGIN: int = 12
    _SPACING: int = 12

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le workspace avec un layout horizontal vide.

        Args:
            parent: Widget parent éventuel.
        """
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(
            self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN
        )
        self._layout.setSpacing(self._SPACING)

    def layout(self) -> QHBoxLayout:
        """Retourne le layout principal du workspace.

        Returns:
            Le ``QHBoxLayout`` du workspace.
        """
        return self._layout

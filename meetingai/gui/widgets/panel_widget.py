"""Classe de base pour les panneaux de l'interface MeetingAI."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PanelWidget(QWidget):
    """Panneau affichant un titre centré et une zone de contenu remplaçable.

    Cette classe de base évite la duplication entre les différents panneaux
    de l'application (transcription, résumé, historique). Elle expose une
    méthode ``set_content`` permettant de remplacer ultérieurement le contenu
    central par un widget métier sans modifier la structure du panneau.

    Args:
        title: Texte affiché en en-tête du panneau.
        parent: Widget parent éventuel.
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        """Initialise le panneau avec son titre centré."""
        super().__init__(parent)
        self._setup_ui(title)

    def _setup_ui(self, title: str) -> None:
        """Construit le layout vertical avec le titre et la zone de contenu."""
        main_layout = QVBoxLayout(self)
        self._title_label = QLabel(title, self)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._title_label)

        self._content_layout = QVBoxLayout()
        main_layout.addLayout(self._content_layout)
        main_layout.setStretchFactor(self._content_layout, 1)

    def set_content(self, widget: QWidget) -> None:
        """Remplace le contenu central du panneau.

        Args:
            widget: Widget à afficher dans le panneau.
        """
        self._clear_content()
        self._content_layout.addWidget(widget)

    def _clear_content(self) -> None:
        """Supprime les widgets actuellement présents dans la zone de contenu."""
        while (item := self._content_layout.takeAt(0)) is not None:
            if child := item.widget():
                child.deleteLater()

"""Classe de base pour les panneaux de l'interface MeetingAI."""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QWidget


class PanelWidget(QGroupBox):
    """Panneau groupé affichant un titre et une zone de contenu remplaçable.

    Cette classe de base évite la duplication entre les différents panneaux
    de l'application (transcription, résumé, historique). Le titre est intégré
    dans la bordure du ``QGroupBox``. Elle expose une méthode ``set_content``
    permettant de remplacer le contenu central par un widget métier sans
    modifier la structure du panneau.

    Args:
        title: Texte affiché dans l'en-tête du panneau.
        parent: Widget parent éventuel.
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        """Initialise le panneau avec son titre."""
        super().__init__(title, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construit le layout vertical avec la zone de contenu."""
        self.setStyleSheet(
            "QGroupBox {"
            "  border: 1px solid #ced4da;"
            "  border-radius: 6px;"
            "  background-color: #ffffff;"
            "  font-weight: bold;"
            "  font-size: 14px;"
            "  margin-top: 12px;"
            "  padding-top: 8px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 4px 8px;"
            "  color: #212529;"
            "}"
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(0)
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

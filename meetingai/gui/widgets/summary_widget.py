"""Panneau destiné à afficher le résumé IA."""

from PySide6.QtWidgets import QLabel

from meetingai.gui.widgets.panel_widget import PanelWidget
from meetingai.services.summarization.summary_result import SummaryResult


class SummaryWidget(PanelWidget):
    """Panneau de résumé IA.

    Ce widget affiche le texte résumé lorsqu'un résultat est fourni via
    ``set_summary``.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: object | None = None) -> None:
        """Initialise le panneau de résumé IA."""
        super().__init__("Résumé IA", parent)

    def set_summary(self, result: SummaryResult) -> None:
        """Affiche le texte du résumé.

        Args:
            result: Résultat du résumé à afficher.
        """
        label = QLabel(result.text)
        label.setWordWrap(True)
        self.set_content(label)

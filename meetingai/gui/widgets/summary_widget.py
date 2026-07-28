"""Panneau destiné à afficher le résumé IA."""

from meetingai.gui.widgets.panel_widget import PanelWidget


class SummaryWidget(PanelWidget):
    """Panneau de résumé IA.

    Ce widget est actuellement un simple panneau titré. Il sera enrichi
    ultérieurement avec la zone de résumé provenant du service correspondant.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: object | None = None) -> None:
        """Initialise le panneau de résumé IA."""
        super().__init__("Résumé IA", parent)

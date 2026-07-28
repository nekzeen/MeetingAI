"""Panneau destiné à afficher l'historique des projets."""

from meetingai.gui.widgets.panel_widget import PanelWidget


class HistoryWidget(PanelWidget):
    """Panneau d'historique.

    Ce widget est actuellement un simple panneau titré. Il sera enrichi
    ultérieurement avec la liste des projets ou fichiers récents.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: object | None = None) -> None:
        """Initialise le panneau d'historique."""
        super().__init__("Historique", parent)

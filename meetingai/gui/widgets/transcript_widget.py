"""Panneau destiné à afficher la transcription."""

from meetingai.gui.widgets.panel_widget import PanelWidget


class TranscriptWidget(PanelWidget):
    """Panneau de transcription.

    Ce widget est actuellement un simple panneau titré. Il sera enrichi
    ultérieurement avec la zone de transcription provenant du service
    correspondant.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: object | None = None) -> None:
        """Initialise le panneau de transcription."""
        super().__init__("Transcription", parent)

"""Panneau destiné à afficher la transcription."""

from PySide6.QtWidgets import QLabel

from meetingai.gui.widgets.panel_widget import PanelWidget
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TranscriptWidget(PanelWidget):
    """Panneau de transcription.

    Ce widget affiche le texte transcrit lorsqu'un résultat est fourni via
    ``set_transcription``. Il sera enrichi ultérieurement avec un affichage
    plus avancé.

    Args:
        parent: Widget parent éventuel.
    """

    def __init__(self, parent: object | None = None) -> None:
        """Initialise le panneau de transcription."""
        super().__init__("Transcription", parent)

    def set_transcription(self, result: TranscriptionResult) -> None:
        """Affiche le texte de la transcription.

        Args:
            result: Résultat de transcription à afficher.
        """
        label = QLabel(result.text)
        label.setWordWrap(True)
        self.set_content(label)

"""Application PySide6 de MeetingAI."""

from PySide6.QtWidgets import QApplication

from meetingai.gui.main_window import MainWindow


class MeetingAIApplication(QApplication):
    """Point d'entrée de l'application graphique MeetingAI.

    Configure les métadonnées de l'application et affiche la fenêtre
    principale.
    """

    def __init__(self) -> None:
        """Initialise l'application et la fenêtre principale."""
        super().__init__([])
        self.setApplicationName("MeetingAI")
        self.setOrganizationName("Gaël Morvan")
        self.setOrganizationDomain("github.com/nekzeen")

        self._main_window = MainWindow()
        self._main_window.show()

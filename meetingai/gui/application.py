"""Application PySide6 de MeetingAI."""

from PySide6.QtWidgets import QApplication

from meetingai.core.application_context import ApplicationContext
from meetingai.gui.main_window import MainWindow


class MeetingAIApplication(QApplication):
    """Point d'entrée de l'application graphique MeetingAI.

    Configure les métadonnées de l'application, crée le contexte applicatif
    racine et affiche la fenêtre principale.
    """

    def __init__(self) -> None:
        """Initialise l'application et la fenêtre principale."""
        super().__init__([])
        self.setApplicationName("MeetingAI")
        self.setOrganizationName("Gaël Morvan")
        self.setOrganizationDomain("github.com/nekzeen")

        self._context = ApplicationContext()
        self._main_window = MainWindow()
        self._main_window.show()

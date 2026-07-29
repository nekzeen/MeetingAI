"""Tests du widget de résumé IA."""

import unittest

from PySide6.QtWidgets import QApplication, QLabel

from meetingai.gui.widgets.summary_widget import SummaryWidget
from meetingai.services.summarization.summary_result import SummaryResult


class TestSummaryWidget(unittest.TestCase):
    """Tests d'affichage du résumé IA."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Instancie le widget de résumé."""
        self.widget = SummaryWidget()

    def tearDown(self) -> None:
        """Ferme et détruit le widget."""
        self.widget.close()
        self.widget.deleteLater()

    def test_set_summary_displays_text(self) -> None:
        """set_summary affiche le texte du résumé."""
        result = SummaryResult(
            text="Résumé important.",
            provider="fake",
        )

        self.widget.set_summary(result)

        labels = self.widget.findChildren(QLabel)
        texts = [label.text() for label in labels]
        self.assertIn("Résumé important.", texts)


if __name__ == "__main__":
    unittest.main()

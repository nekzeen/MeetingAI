"""Tests de l'exporteur au format texte brut."""

import tempfile
import unittest
from pathlib import Path

from meetingai.services.export.txt_exporter import TxtExporter
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestTxtExporter(unittest.TestCase):
    """Tests de l'exporteur TXT."""

    def _build_result(self) -> TranscriptionResult:
        """Construit un résultat de transcription factice."""
        return TranscriptionResult(
            text="Bonjour le monde.",
            language="fr",
            duration=1.5,
            model="fake",
            processing_time=0.1,
            metadata={},
        )

    def test_extension_is_txt(self) -> None:
        """L'extension de fichier est ``.txt``."""
        exporter = TxtExporter()

        self.assertEqual(exporter.extension, ".txt")

    def test_export_writes_text_content(self) -> None:
        """L'export écrit le texte de la transcription dans le fichier."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "transcription.txt"
            exporter = TxtExporter()
            result = self._build_result()

            exporter.export(result, output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "Bonjour le monde.",
            )

    def test_export_creates_parent_directory(self) -> None:
        """L'export crée les répertoires parents si nécessaire."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "nested" / "transcription.txt"
            exporter = TxtExporter()

            exporter.export(self._build_result(), output_path)

            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()

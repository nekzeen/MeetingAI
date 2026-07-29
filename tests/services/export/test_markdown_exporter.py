"""Tests de l'exporteur au format Markdown."""

import tempfile
import unittest
from pathlib import Path

from meetingai.services.export.markdown_exporter import MarkdownExporter
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestMarkdownExporter(unittest.TestCase):
    """Tests de l'exporteur Markdown."""

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

    def test_extension_is_md(self) -> None:
        """L'extension de fichier est ``.md``."""
        exporter = MarkdownExporter()

        self.assertEqual(exporter.extension, ".md")

    def test_export_writes_markdown_content(self) -> None:
        """L'export écrit un contenu Markdown structuré."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "transcription.md"
            exporter = MarkdownExporter()
            result = self._build_result()

            exporter.export(result, output_path)

            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# Transcription", content)
            self.assertIn("## Métadonnées", content)
            self.assertIn("Bonjour le monde.", content)
            self.assertIn("Langue", content)
            self.assertIn("Modèle", content)

    def test_export_creates_parent_directory(self) -> None:
        """L'export crée les répertoires parents si nécessaire."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "nested" / "transcription.md"
            exporter = MarkdownExporter()

            exporter.export(self._build_result(), output_path)

            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()

"""Tests du service d'export."""

import tempfile
import unittest
from pathlib import Path

from meetingai.services.export.export_service import ExportService
from meetingai.services.export.markdown_exporter import MarkdownExporter
from meetingai.services.export.txt_exporter import TxtExporter
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestExportService(unittest.TestCase):
    """Tests du service d'export des transcriptions."""

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

    def test_supported_formats_includes_txt_and_markdown(self) -> None:
        """Les formats TXT et Markdown sont supportés par défaut."""
        service = ExportService()

        formats = service.supported_formats()

        self.assertIn("txt", formats)
        self.assertIn("markdown", formats)

    def test_extension_for_txt(self) -> None:
        """L'extension du format TXT est ``.txt``."""
        service = ExportService()

        self.assertEqual(service.extension_for("txt"), ".txt")

    def test_extension_for_markdown(self) -> None:
        """L'extension du format Markdown est ``.md``."""
        service = ExportService()

        self.assertEqual(service.extension_for("markdown"), ".md")

    def test_export_txt(self) -> None:
        """L'export TXT produit un fichier texte."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "transcription.txt"
            service = ExportService()

            service.export(self._build_result(), output_path, "txt")

            self.assertTrue(output_path.exists())
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "Bonjour le monde.",
            )

    def test_export_markdown(self) -> None:
        """L'export Markdown produit un fichier Markdown."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "transcription.md"
            service = ExportService()

            service.export(self._build_result(), output_path, "markdown")

            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# Transcription", content)

    def test_export_unknown_format_raises(self) -> None:
        """Un format inconnu lève une erreur explicite."""
        service = ExportService()

        with self.assertRaises(ValueError) as context:
            service.export(
                self._build_result(),
                Path("/tmp/output.pdf"),
                "pdf",
            )

        self.assertIn("pdf", str(context.exception))

    def test_register_custom_exporter(self) -> None:
        """Un nouvel exporteur peut être enregistré dynamiquement."""
        class _CustomExporter:
            extension = ".custom"

            def export(
                self,
                result: TranscriptionResult,
                output_path: Path,
            ) -> None:
                output_path.write_text(result.text, encoding="utf-8")

        service = ExportService()
        service.register_exporter("custom", _CustomExporter())

        self.assertIn("custom", service.supported_formats())
        self.assertEqual(service.extension_for("custom"), ".custom")


if __name__ == "__main__":
    unittest.main()

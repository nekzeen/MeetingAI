"""Tests du contrôleur d'export."""

import tempfile
import unittest
from pathlib import Path

from meetingai.config.config_manager import ConfigManager
from meetingai.controllers.export_controller import ExportController
from meetingai.services.export.export_service import ExportService
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestExportController(unittest.TestCase):
    """Tests du contrôleur d'export."""

    def setUp(self) -> None:
        """Prépare un répertoire temporaire pour la configuration."""
        self._temp_dir = tempfile.TemporaryDirectory()
        config_path = Path(self._temp_dir.name) / "config.json"
        self.config_manager = ConfigManager(config_path)
        self.export_service = ExportService()
        self.controller = ExportController(
            export_service=self.export_service,
            config_manager=self.config_manager,
        )

    def tearDown(self) -> None:
        """Nettoie le répertoire temporaire."""
        self._temp_dir.cleanup()

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

    def test_export_txt_without_result_emits_failed(self) -> None:
        """L'export sans transcription émet un signal d'échec."""
        emitted: list[str] = []
        self.controller.export_failed.connect(emitted.append)

        self.controller.export_txt()

        self.assertEqual(len(emitted), 1)
        self.assertIn("Aucune transcription", emitted[0])

    def test_export_txt_emits_succeeded(self) -> None:
        """L'export TXT émet le chemin du fichier créé."""
        self.controller.on_transcription_ready(self._build_result())
        emitted: list[str] = []
        self.controller.export_succeeded.connect(emitted.append)

        self.controller.export_txt()

        self.assertEqual(len(emitted), 1)
        self.assertTrue(Path(emitted[0]).exists())
        self.assertEqual(Path(emitted[0]).suffix, ".txt")

    def test_export_markdown_emits_succeeded(self) -> None:
        """L'export Markdown émet le chemin du fichier créé."""
        self.controller.on_transcription_ready(self._build_result())
        emitted: list[str] = []
        self.controller.export_succeeded.connect(emitted.append)

        self.controller.export_markdown()

        self.assertEqual(len(emitted), 1)
        self.assertTrue(Path(emitted[0]).exists())
        self.assertEqual(Path(emitted[0]).suffix, ".md")

    def test_export_error_emits_failed(self) -> None:
        """Une erreur d'écriture émet un signal d'échec."""
        self.controller.on_transcription_ready(self._build_result())
        emitted: list[str] = []
        self.controller.export_failed.connect(emitted.append)

        def _raise_error(
            result: TranscriptionResult,
            output_path: Path,
            format_name: str,
        ) -> None:
            raise RuntimeError("écriture impossible")

        self.export_service.export = _raise_error

        self.controller.export_txt()

        self.assertEqual(len(emitted), 1)
        self.assertIn("écriture impossible", emitted[0])


if __name__ == "__main__":
    unittest.main()

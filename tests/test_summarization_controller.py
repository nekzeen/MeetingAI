"""Tests du contrôleur de résumé IA."""

import tempfile
import unittest
from pathlib import Path

from meetingai.config.config_manager import ConfigManager
from meetingai.controllers.summarization_controller import (
    SummarizationController,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)
from meetingai.services.summarization.summary_result import SummaryResult
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)
from meetingai.services.summarization.summarization_service import (
    SummarizationService,
)


class TestSummarizationController(unittest.TestCase):
    """Tests du contrôleur de résumé IA."""

    def setUp(self) -> None:
        """Prépare un contrôleur avec une configuration temporaire."""
        self._temp_dir = tempfile.TemporaryDirectory()
        config_path = Path(self._temp_dir.name) / "config.json"
        self.config_manager = ConfigManager(config_path)
        self.factory = SummarizationFactory()
        self.controller = SummarizationController(
            factory=self.factory,
            config_manager=self.config_manager,
        )

    def tearDown(self) -> None:
        """Nettoie le répertoire temporaire."""
        self._temp_dir.cleanup()

    def _build_transcription(self) -> TranscriptionResult:
        """Construit un résultat de transcription factice."""
        return TranscriptionResult(
            text="Ceci est un texte long à résumer.",
            language="fr",
            duration=10.0,
            model="fake",
            processing_time=0.1,
            metadata={},
        )

    def test_summarize_without_transcription_emits_failed(self) -> None:
        """Le résumé sans transcription émet un signal d'échec."""
        emitted: list[str] = []
        self.controller.summary_failed.connect(emitted.append)

        self.controller.summarize_current_transcription()

        self.assertEqual(len(emitted), 1)
        self.assertIn("Aucune transcription", emitted[0])

    def test_summarize_emits_summary_ready(self) -> None:
        """Le résumé d'une transcription émet summary_ready."""
        self.controller.on_transcription_ready(self._build_transcription())
        emitted: list[object] = []
        self.controller.summary_ready.connect(emitted.append)

        self.controller.summarize_current_transcription()

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].text, "Ceci est un résumé simulé.")
        self.assertEqual(emitted[0].provider, "fake")

    def test_summarize_uses_configured_provider(self) -> None:
        """Le contrôleur utilise le provider configuré."""
        class _CustomSummarizationService(SummarizationService):
            def name(self) -> str:
                return "custom"

            def is_available(self) -> bool:
                return True

            def summarize(self, text: str) -> SummaryResult:
                return SummaryResult(text="résumé custom", provider="custom")

        self.factory.register_provider("custom", _CustomSummarizationService)
        self.config_manager.set("summarization.provider", "custom")
        self.controller.on_transcription_ready(self._build_transcription())
        emitted: list[object] = []
        self.controller.summary_ready.connect(emitted.append)

        self.controller.summarize_current_transcription()

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].text, "résumé custom")


if __name__ == "__main__":
    unittest.main()

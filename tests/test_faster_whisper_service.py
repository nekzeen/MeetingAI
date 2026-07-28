"""Tests de l'implémentation FasterWhisperService."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from meetingai.core.task import Task
from meetingai.models.media_file import MediaFile
from meetingai.services.speech_to_text.faster_whisper_service import (
    FasterWhisperService,
    _FASTER_WHISPER,
)


class TestFasterWhisperService(unittest.TestCase):
    """Tests du service de transcription faster-whisper."""

    def test_name_returns_faster_whisper(self) -> None:
        """Le service retourne le nom attendu."""
        service = FasterWhisperService()

        self.assertEqual(service.name(), "FasterWhisper")

    def test_version_reflects_environment(self) -> None:
        """La version reflète la disponibilité de la bibliothèque."""
        service = FasterWhisperService()

        if _FASTER_WHISPER is None:
            self.assertEqual(service.version(), "unknown")
        else:
            self.assertNotEqual(service.version(), "unknown")

    def test_supported_languages_is_non_empty_list(self) -> None:
        """Le service expose une liste de langues supportées."""
        service = FasterWhisperService()
        languages = service.supported_languages()

        self.assertIsInstance(languages, list)
        self.assertIn("fr", languages)
        self.assertIn("en", languages)

    def test_is_available_reflects_environment(self) -> None:
        """La disponibilité dépend de la présence de faster-whisper."""
        service = FasterWhisperService()

        self.assertEqual(service.is_available(), _FASTER_WHISPER is not None)

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_is_available_true_when_module_mocked(self) -> None:
        """is_available retourne True lorsque le module est présent."""
        service = FasterWhisperService()

        self.assertTrue(service.is_available())

    def test_transcribe_without_loaded_model_raises(self) -> None:
        """transcribe échoue explicitement si aucun modèle n'est chargé."""
        service = FasterWhisperService()
        media = MagicMock(spec=MediaFile)
        task = MagicMock(spec=Task)

        with self.assertRaises(RuntimeError) as context:
            service.transcribe(media, task)

        self.assertIn("modèle faster-whisper", str(context.exception).lower())

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_load_model_uses_local_files_only(self) -> None:
        """load_model charge le modèle depuis le répertoire configuré."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )

            service.load_model()

            self.assertIsNotNone(service._model)
            from meetingai.services.speech_to_text import faster_whisper_service

            faster_whisper_service._FASTER_WHISPER.WhisperModel.assert_called_once_with(
                str(model_dir),
                device="cpu",
                compute_type="int8",
                local_files_only=True,
            )


if __name__ == "__main__":
    unittest.main()

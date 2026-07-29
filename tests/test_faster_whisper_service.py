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

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_transcribe_automatically_loads_model(self) -> None:
        """transcribe charge le modèle automatiquement au premier appel."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )
            media = MagicMock(spec=MediaFile)
            media.path = Path("/tmp/audio.mp3")
            task = MagicMock(spec=Task)

            from meetingai.services.speech_to_text import faster_whisper_service

            mock_info = MagicMock()
            mock_info.language = "fr"
            mock_info.duration = 1.0
            mock_info.language_probability = 0.9
            faster_whisper_service._FASTER_WHISPER.WhisperModel.return_value.transcribe.return_value = (
                [],
                mock_info,
            )

            result = service.transcribe(media, task)

            self.assertIsNotNone(service._model)
            self.assertEqual(result.model, "tiny")

            faster_whisper_service._FASTER_WHISPER.WhisperModel.assert_called_once_with(
                str(model_dir),
                device="cpu",
                compute_type="int8",
                local_files_only=True,
            )

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_transcribe_reuses_loaded_model(self) -> None:
        """transcribe ne recharge pas le modèle s'il est déjà chargé."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )
            media = MagicMock(spec=MediaFile)
            media.path = Path("/tmp/audio.mp3")
            task = MagicMock(spec=Task)

            from meetingai.services.speech_to_text import faster_whisper_service

            mock_info = MagicMock()
            mock_info.language = "fr"
            mock_info.duration = 1.0
            mock_info.language_probability = 0.9
            faster_whisper_service._FASTER_WHISPER.WhisperModel.return_value.transcribe.return_value = (
                [],
                mock_info,
            )

            service.transcribe(media, task)
            service.transcribe(media, task)

            faster_whisper_service._FASTER_WHISPER.WhisperModel.assert_called_once()

    def test_is_model_present_false_when_missing(self) -> None:
        """is_model_present retourne False si le répertoire n'existe pas."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )

            self.assertFalse(service.is_model_present())

    def test_is_model_present_true_when_exists(self) -> None:
        """is_model_present retourne True si le répertoire du modèle existe."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )

            self.assertTrue(service.is_model_present())

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_load_model_error_includes_model_name_and_path(self) -> None:
        """load_model indique le nom du modèle et l'emplacement recherché."""
        from meetingai.services.speech_to_text import faster_whisper_service

        faster_whisper_service._FASTER_WHISPER.WhisperModel.side_effect = (
            RuntimeError("network unreachable")
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )

            with self.assertRaises(RuntimeError) as context:
                service.load_model()

            error_message = str(context.exception).lower()
            self.assertIn("tiny", error_message)
            self.assertIn(str(tmp_dir).lower(), error_message)
            self.assertIn("téléchargez", error_message)
            self.assertIn("download_model", error_message)

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_transcribe_reports_error_when_model_missing(self) -> None:
        """transcribe retourne une erreur explicite si le modèle est introuvable."""
        from meetingai.services.speech_to_text import faster_whisper_service

        faster_whisper_service._FASTER_WHISPER.WhisperModel.side_effect = (
            RuntimeError("network unreachable")
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )
            media = MagicMock(spec=MediaFile)
            task = MagicMock(spec=Task)

            with self.assertRaises(RuntimeError) as context:
                service.transcribe(media, task)

            error_message = str(context.exception).lower()
            self.assertIn("tiny", error_message)
            self.assertIn(str(tmp_dir).lower(), error_message)
            self.assertIn("téléchargez", error_message)
            self.assertIn("download_model", error_message)

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=None,
    )
    def test_transcribe_reports_error_when_library_unavailable(self) -> None:
        """transcribe retourne une erreur explicite si la bibliothèque est absente."""
        service = FasterWhisperService()
        media = MagicMock(spec=MediaFile)
        task = MagicMock(spec=Task)

        with self.assertRaises(RuntimeError) as context:
            service.transcribe(media, task)

        self.assertIn("bibliothèque", str(context.exception).lower())

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=None,
    )
    def test_download_model_raises_when_library_unavailable(self) -> None:
        """download_model refuse de télécharger si la bibliothèque est absente."""
        with self.assertRaises(RuntimeError) as context:
            FasterWhisperService.download_model()

        self.assertIn("bibliothèque", str(context.exception).lower())

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_download_model_delegates_to_faster_whisper(self) -> None:
        """download_model délègue le téléchargement à faster-whisper."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from meetingai.services.speech_to_text import faster_whisper_service

            faster_whisper_service._FASTER_WHISPER.download_model.return_value = (
                str(Path(tmp_dir) / "tiny")
            )

            path = FasterWhisperService.download_model(
                model_size="tiny",
                models_directory=tmp_dir,
            )

            self.assertEqual(path, Path(tmp_dir) / "tiny")
            faster_whisper_service._FASTER_WHISPER.download_model.assert_called_once_with(
                "tiny", output_dir=Path(tmp_dir)
            )

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_transcribe_reports_progress_via_callback(self) -> None:
        """transcribe notifie la progression à partir des segments."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )
            media = MagicMock(spec=MediaFile)
            media.path = Path("/tmp/audio.mp3")
            task = MagicMock(spec=Task)

            from meetingai.services.speech_to_text import faster_whisper_service

            segment1 = MagicMock()
            segment1.text = " Bonjour "
            segment1.start = 0.0
            segment1.end = 0.5
            segment2 = MagicMock()
            segment2.text = " le monde "
            segment2.start = 0.5
            segment2.end = 1.0
            info = MagicMock()
            info.language = "fr"
            info.duration = 1.0
            info.language_probability = 0.95
            faster_whisper_service._FASTER_WHISPER.WhisperModel.return_value.transcribe.return_value = (
                [segment1, segment2],
                info,
            )

            progress_values: list[int] = []

            service.transcribe(
                media,
                task,
                progress_callback=progress_values.append,
            )

            self.assertIn(50, progress_values)
            self.assertIn(100, progress_values)

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_transcribe_sends_final_progress_when_no_segments(self) -> None:
        """transcribe envoie 100% même sans segment."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )
            media = MagicMock(spec=MediaFile)
            media.path = Path("/tmp/audio.mp3")
            task = MagicMock(spec=Task)

            from meetingai.services.speech_to_text import faster_whisper_service

            info = MagicMock()
            info.language = "fr"
            info.duration = 1.0
            info.language_probability = 0.95
            faster_whisper_service._FASTER_WHISPER.WhisperModel.return_value.transcribe.return_value = (
                [],
                info,
            )

            progress_values: list[int] = []

            service.transcribe(
                media,
                task,
                progress_callback=progress_values.append,
            )

            self.assertEqual(progress_values, [100])

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

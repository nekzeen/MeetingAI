"""Tests de la transcription réelle avec FasterWhisperService."""

import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

from meetingai.core.task import Task
from meetingai.models.media_file import MediaFile, MediaType
from meetingai.services.speech_to_text.faster_whisper_service import (
    FasterWhisperService,
    _FASTER_WHISPER,
)
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class TestFasterWhisperModelLoading(unittest.TestCase):
    """Tests du chargement du modèle faster-whisper."""

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_load_model_raises_when_directory_missing(self) -> None:
        """load_model échoue proprement si le modèle n'est ni local ni accessible."""
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
            self.assertIn("téléchargez", error_message)
            self.assertIn("download_model", error_message)

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=None,
    )
    def test_transcribe_reports_error_when_model_unavailable(self) -> None:
        """transcribe retourne une erreur explicite si la bibliothèque est absente."""
        service = FasterWhisperService()
        media = MagicMock(spec=MediaFile)
        task = MagicMock(spec=Task)

        with self.assertRaises(RuntimeError) as context:
            service.transcribe(media, task)

        self.assertIn("bibliothèque", str(context.exception).lower())


class TestFasterWhisperTranscription(unittest.TestCase):
    """Tests de la transcription via FasterWhisperService."""

    def _build_mock_model(self) -> MagicMock:
        """Construit un modèle faster-whisper simulé."""
        segment = MagicMock()
        segment.text = " Bonjour "
        segment.start = 0.0
        segment.end = 1.5
        info = MagicMock()
        info.language = "fr"
        info.duration = 1.5
        info.language_probability = 0.95

        model = MagicMock()
        model.transcribe.return_value = ([segment], info)
        return model

    @patch(
        "meetingai.services.speech_to_text.faster_whisper_service._FASTER_WHISPER",
        new=MagicMock(),
    )
    def test_transcribe_returns_complete_result(self) -> None:
        """transcribe retourne un TranscriptionResult correctement rempli."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_dir = Path(tmp_dir) / "tiny"
            model_dir.mkdir()
            service = FasterWhisperService(
                model_size="tiny",
                models_directory=tmp_dir,
            )
            service._model = self._build_mock_model()

            media = MediaFile(
                path=Path("/tmp/audio.mp3").resolve(),
                name="audio.mp3",
                extension=".mp3",
                size=1234,
                media_type=MediaType.AUDIO,
            )
            task = Task(name="transcription")

            result = service.transcribe(media, task)

            self.assertIsInstance(result, TranscriptionResult)
            self.assertEqual(result.text, "Bonjour")
            self.assertEqual(result.language, "fr")
            self.assertEqual(result.duration, 1.5)
            self.assertEqual(result.model, "tiny")
            self.assertGreaterEqual(result.processing_time, 0.0)
            self.assertEqual(result.metadata["language_probability"], 0.95)
            self.assertEqual(task.progress, 100)

    @unittest.skipUnless(
        os.environ.get("MEETINGAI_WHISPER_MODEL") is not None,
        "Variable MEETINGAI_WHISPER_MODEL non définie : test réel ignoré.",
    )
    @unittest.skipUnless(
        _FASTER_WHISPER is not None,
        "faster-whisper non installé : test réel ignoré.",
    )
    def test_real_transcription_with_local_model(self) -> None:
        """Transcription réelle d'un petit fichier audio avec un modèle local."""
        model_path = Path(os.environ["MEETINGAI_WHISPER_MODEL"])
        models_directory = model_path.parent
        model_size = model_path.name

        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "test.wav"
            self._write_sine_wave(audio_path)

            service = FasterWhisperService(
                model_size=model_size,
                models_directory=models_directory,
                device="cpu",
                compute_type="int8",
            )
            service.load_model()

            media = MediaFile(
                path=audio_path,
                name="test.wav",
                extension=".wav",
                size=audio_path.stat().st_size,
                media_type=MediaType.AUDIO,
            )
            task = Task(name="transcription")

            result = service.transcribe(media, task)

            self.assertIsInstance(result, TranscriptionResult)
            self.assertIsInstance(result.text, str)
            self.assertGreater(len(result.text), 0)
            self.assertEqual(result.model, model_size)
            self.assertGreaterEqual(result.processing_time, 0.0)

    @staticmethod
    def _write_sine_wave(path: Path) -> None:
        """Écrit un court fichier WAV mono 16 bits."""
        duration_seconds = 1
        sample_rate = 16000
        num_samples = duration_seconds * sample_rate

        with wave.open(str(path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            import audioop  # noqa: PLC0415
            import struct  # noqa: PLC0415

            samples = []
            for i in range(num_samples):
                value = int(0.25 * 32767 * ((i * 2) % 2 * 2 - 1))
                samples.append(struct.pack("<h", value))
            wav_file.writeframes(audioop.lin2lin(b"".join(samples), 2, 2))


if __name__ == "__main__":
    unittest.main()

"""Tests de la factory Speech-To-Text."""

import unittest
from unittest.mock import MagicMock, patch

from meetingai.config.speech_to_text_configuration import (
    SpeechToTextConfiguration,
)
from meetingai.services.speech_to_text.fake_speech_to_text_service import (
    FakeSpeechToTextService,
)
from meetingai.services.speech_to_text.faster_whisper_service import (
    FasterWhisperService,
)
from meetingai.services.speech_to_text.speech_to_text_factory import (
    SpeechToTextFactory,
)


class TestSpeechToTextConfiguration(unittest.TestCase):
    """Tests de la dataclass de configuration."""

    def test_default_configuration(self) -> None:
        """La configuration par défaut utilise le provider fake."""
        config = SpeechToTextConfiguration()

        self.assertEqual(config.provider, "fake")
        self.assertEqual(config.model_name, "small")
        self.assertEqual(config.device, "auto")
        self.assertIsNone(config.language)

    def test_with_provider_returns_new_instance(self) -> None:
        """with_provider retourne une nouvelle configuration immuable."""
        base = SpeechToTextConfiguration()
        updated = base.with_provider("faster-whisper")

        self.assertEqual(base.provider, "fake")
        self.assertEqual(updated.provider, "faster-whisper")

    def test_with_options_returns_new_instance(self) -> None:
        """with_options retourne une nouvelle configuration avec options mises à jour."""
        base = SpeechToTextConfiguration()
        updated = base.with_options(model_name="medium", device="cuda")

        self.assertEqual(updated.model_name, "medium")
        self.assertEqual(updated.device, "cuda")
        self.assertEqual(updated.provider, "fake")


class TestSpeechToTextFactory(unittest.TestCase):
    """Tests de la factory de moteurs Speech-To-Text."""

    def test_create_fake_service(self) -> None:
        """La factory retourne un FakeSpeechToTextService pour le provider fake."""
        factory = SpeechToTextFactory()
        config = SpeechToTextConfiguration(provider="fake")

        service = factory.create(config)

        self.assertIsInstance(service, FakeSpeechToTextService)

    def test_create_faster_whisper_service(self) -> None:
        """La factory retourne un FasterWhisperService pour le provider faster-whisper."""
        factory = SpeechToTextFactory()
        config = SpeechToTextConfiguration(
            provider="faster-whisper",
            model_name="tiny",
            device="cpu",
            compute_type="float16",
        )

        service = factory.create(config)

        self.assertIsInstance(service, FasterWhisperService)
        self.assertEqual(service._model_size, "tiny")
        self.assertEqual(service._device, "cpu")
        self.assertEqual(service._compute_type, "float16")

    def test_unknown_provider_raises(self) -> None:
        """Un provider inconnu lève une ValueError explicite."""
        factory = SpeechToTextFactory()
        config = SpeechToTextConfiguration(provider="unknown")

        with self.assertRaises(ValueError) as context:
            factory.create(config)

        self.assertIn("unknown", str(context.exception).lower())

    def test_register_new_provider(self) -> None:
        """Un nouveau provider peut être enregistré sans modifier la factory."""
        factory = SpeechToTextFactory()
        custom = MagicMock(spec=FakeSpeechToTextService)
        custom_builder = MagicMock(return_value=custom)

        factory.register_provider("custom", custom_builder)
        config = SpeechToTextConfiguration(provider="custom")
        service = factory.create(config)

        self.assertIs(service, custom)
        custom_builder.assert_called_once_with(config)


if __name__ == "__main__":
    unittest.main()

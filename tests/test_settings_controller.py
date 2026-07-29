"""Tests du contrôleur de paramètres."""

import tempfile
import unittest
from pathlib import Path

from meetingai.config.config_manager import ConfigManager
from meetingai.controllers.settings_controller import SettingsController
from meetingai.services.speech_to_text.speech_to_text_factory import (
    SpeechToTextFactory,
)
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)


class TestSettingsController(unittest.TestCase):
    """Tests unitaires du contrôleur de paramètres."""

    def setUp(self) -> None:
        """Prépare un répertoire temporaire pour la configuration."""
        self._temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Nettoie le répertoire temporaire."""
        self._temp_dir.cleanup()

    def _build_controller(self) -> tuple[SettingsController, ConfigManager]:
        """Crée un contrôleur associé à une configuration temporaire."""
        config_path = Path(self._temp_dir.name) / "config.json"
        config_manager = ConfigManager(config_path)
        return (
            SettingsController(
                config_manager,
                SpeechToTextFactory(),
                SummarizationFactory(),
            ),
            config_manager,
        )

    def test_load_settings_returns_current_values(self) -> None:
        """load_settings retourne les valeurs actuelles de la configuration."""
        controller, _ = self._build_controller()

        settings = controller.load_settings()

        self.assertIn("theme", settings)
        self.assertIn("language", settings)
        self.assertIn("provider", settings)
        self.assertIn("model_name", settings)
        self.assertIn("device", settings)
        self.assertIn("compute_type", settings)
        self.assertIn("output_directory", settings)
        self.assertIn("summarization_provider", settings)
        self.assertIn("summarization_model", settings)
        self.assertIn("summarization_available_models", settings)
        self.assertIn("summarization_profile", settings)
        self.assertIn("summarization_profiles", settings)

    def test_save_settings_persists_values(self) -> None:
        """save_settings persiste les nouvelles valeurs dans ConfigManager."""
        controller, config_manager = self._build_controller()
        new_settings = {
            "theme": "dark",
            "language": "en",
            "provider": "fake",
            "model_name": "medium",
            "device": "cpu",
            "compute_type": "float16",
            "output_directory": "custom_output",
            "summarization_provider": "fake",
            "summarization_model": "custom-model",
            "summarization_profile": "key_points",
        }

        controller.save_settings(new_settings)

        self.assertEqual(config_manager.get("application.theme"), "dark")
        self.assertEqual(config_manager.get("application.language"), "en")
        self.assertEqual(config_manager.get("speech_to_text.provider"), "fake")
        self.assertEqual(config_manager.get("speech_to_text.model_name"), "medium")
        self.assertEqual(config_manager.get("speech_to_text.device"), "cpu")
        self.assertEqual(config_manager.get("speech_to_text.compute_type"), "float16")
        self.assertEqual(config_manager.get("export.output_directory"), "custom_output")
        self.assertEqual(
            config_manager.get("summarization.provider"), "fake"
        )
        self.assertEqual(
            config_manager.get("summarization.ollama_model"), "custom-model"
        )
        self.assertEqual(
            config_manager.get("summarization.profile"), "key_points"
        )

    def test_save_settings_rejects_invalid_theme(self) -> None:
        """save_settings lève une erreur si le thème n'est pas supporté."""
        controller, _ = self._build_controller()
        settings = controller.load_settings()
        settings["theme"] = "invalid"

        with self.assertRaises(ValueError):
            controller.save_settings(settings)

    def test_save_settings_rejects_invalid_speech_provider(self) -> None:
        """save_settings lève une erreur si le provider STT n'est pas supporté."""
        controller, _ = self._build_controller()
        settings = controller.load_settings()
        settings["provider"] = "unknown"

        with self.assertRaises(ValueError):
            controller.save_settings(settings)

    def test_save_settings_rejects_invalid_summarization_provider(self) -> None:
        """save_settings lève une erreur si le provider de résumé n'est pas supporté."""
        controller, _ = self._build_controller()
        settings = controller.load_settings()
        settings["summarization_provider"] = "unknown"

        with self.assertRaises(ValueError):
            controller.save_settings(settings)

    def test_save_settings_rejects_invalid_summarization_profile(self) -> None:
        """save_settings lève une erreur si le profil de résumé n'est pas supporté."""
        controller, _ = self._build_controller()
        settings = controller.load_settings()
        settings["summarization_profile"] = "unknown"

        with self.assertRaises(ValueError):
            controller.save_settings(settings)

    def test_save_settings_rejects_invalid_device(self) -> None:
        """save_settings lève une erreur si le device n'est pas supporté."""
        controller, _ = self._build_controller()
        settings = controller.load_settings()
        settings["device"] = "tpu"

        with self.assertRaises(ValueError):
            controller.save_settings(settings)

    def test_save_settings_rejects_invalid_compute_type(self) -> None:
        """save_settings lève une erreur si le compute type n'est pas supporté."""
        controller, _ = self._build_controller()
        settings = controller.load_settings()
        settings["compute_type"] = "float64"

        with self.assertRaises(ValueError):
            controller.save_settings(settings)

    def test_available_lists_are_not_empty(self) -> None:
        """Les listes de valeurs disponibles sont peuplées."""
        controller, _ = self._build_controller()

        self.assertIn("light", controller.available_themes())
        self.assertIn("dark", controller.available_themes())
        self.assertIn("fake", controller.available_speech_to_text_providers())
        self.assertIn(
            "faster-whisper", controller.available_speech_to_text_providers()
        )
        self.assertIn("fake", controller.available_summarization_providers())
        self.assertIn("cpu", controller.available_devices())
        self.assertIn("int8", controller.available_compute_types())


if __name__ == "__main__":
    unittest.main()

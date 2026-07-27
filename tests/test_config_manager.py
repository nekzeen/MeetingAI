"""Tests unitaires du gestionnaire de configuration."""

import json
import tempfile
import unittest
from pathlib import Path

from meetingai.config.config_manager import ConfigManager


class TestConfigManagerCreation(unittest.TestCase):
    """Tests liés à la création du gestionnaire."""

    def test_creates_default_file_when_missing(self) -> None:
        """La configuration par défaut est créée si le fichier est absent."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            manager = ConfigManager(config_path)

            self.assertTrue(config_path.exists())
            self.assertEqual(manager.get("application.theme"), "light")
            self.assertEqual(manager.get("transcription.model"), "small")

    def test_all_default_sections_present(self) -> None:
        """Toutes les sections par défaut sont présentes au chargement."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = ConfigManager(Path(tmp_dir) / "config.json")

            self.assertEqual(manager.get("application.language"), "fr")
            self.assertEqual(manager.get("transcription.device"), "cpu")
            self.assertEqual(manager.get("export.output_directory"), "output")
            self.assertEqual(manager.get("logging.level"), "INFO")


class TestConfigManagerLoading(unittest.TestCase):
    """Tests liés au chargement de la configuration."""

    def test_loads_existing_values(self) -> None:
        """Les valeurs existantes sont conservées lors du chargement."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            data = {
                "application": {"theme": "dark"},
                "transcription": {"model": "medium"},
            }
            config_path.write_text(json.dumps(data), encoding="utf-8")

            manager = ConfigManager(config_path)

            self.assertEqual(manager.get("application.theme"), "dark")
            self.assertEqual(manager.get("transcription.model"), "medium")

    def test_missing_keys_get_default_values(self) -> None:
        """Les clés manquantes sont complétées avec les valeurs par défaut."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(json.dumps({}), encoding="utf-8")

            manager = ConfigManager(config_path)

            self.assertEqual(manager.get("application.language"), "fr")
            self.assertEqual(manager.get("logging.level"), "INFO")


class TestConfigManagerModification(unittest.TestCase):
    """Tests liés à la modification de la configuration."""

    def test_set_updates_value(self) -> None:
        """La méthode ``set`` modifie une valeur existante."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = ConfigManager(Path(tmp_dir) / "config.json")
            manager.set("application.theme", "dark")

            self.assertEqual(manager.get("application.theme"), "dark")

    def test_set_raises_on_unknown_section(self) -> None:
        """La méthode ``set`` refuse une section inconnue."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = ConfigManager(Path(tmp_dir) / "config.json")

            with self.assertRaises(KeyError):
                manager.set("unknown.param", "value")


class TestConfigManagerPersistence(unittest.TestCase):
    """Tests liés à la persistance de la configuration."""

    def test_save_persists_changes(self) -> None:
        """Les modifications sont sauvegardées et peuvent être relues."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            manager = ConfigManager(config_path)
            manager.set("application.theme", "dark")
            manager.set("logging.level", "DEBUG")
            manager.save()

            reloaded = ConfigManager(config_path)
            self.assertEqual(reloaded.get("application.theme"), "dark")
            self.assertEqual(reloaded.get("logging.level"), "DEBUG")

    def test_file_contains_valid_json(self) -> None:
        """Le fichier de configuration est un JSON valide."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            ConfigManager(config_path)

            content = config_path.read_text(encoding="utf-8")
            data = json.loads(content)
            self.assertIn("application", data)
            self.assertIn("transcription", data)


if __name__ == "__main__":
    unittest.main()

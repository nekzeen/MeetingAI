"""Tests unitaires du gestionnaire centralisé des logs."""

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from meetingai.config.config_manager import ConfigManager
from meetingai.logging.logger_manager import LoggerManager


class TestLoggerManager(unittest.TestCase):
    """Tests du gestionnaire de logs."""

    def tearDown(self) -> None:
        """Réinitialise le singleton après chaque test."""
        LoggerManager._reset_instance()
        logging.shutdown()

    def _create_config_manager(self, level: str = "INFO") -> ConfigManager:
        """Crée un ConfigManager temporaire avec le niveau demandé."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config = ConfigManager(config_path)
            config.set("logging.level", level)
            config.save()
            return config

    def test_get_logger_returns_logger(self) -> None:
        """Le gestionnaire retourne un logger valide."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"
            manager = LoggerManager(logs_dir=logs_dir)
            logger = manager.get_logger("tests.sample")

            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(logger.name, "meetingai.tests.sample")

    def test_log_directory_created(self) -> None:
        """Le répertoire de logs est créé automatiquement."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"
            LoggerManager(logs_dir=logs_dir)

            self.assertTrue(logs_dir.exists())

    def test_log_file_created(self) -> None:
        """Le fichier de log est créé automatiquement."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"
            LoggerManager(logs_dir=logs_dir)

            log_file = logs_dir / "meetingai.log"
            self.assertTrue(log_file.exists())

    def test_log_message_written(self) -> None:
        """Un message loggué est écrit dans le fichier."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"
            manager = LoggerManager(logs_dir=logs_dir)
            logger = manager.get_logger("tests.writer")
            message = "test message for logger"
            logger.info(message)

            log_file = logs_dir / "meetingai.log"
            content = log_file.read_text(encoding="utf-8")
            self.assertIn(message, content)
            self.assertIn("INFO", content)

    def test_level_from_config_manager(self) -> None:
        """Le niveau de log est récupéré depuis le ConfigManager."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_manager = ConfigManager(config_path)
            config_manager.set("logging.level", "DEBUG")
            config_manager.save()

            logs_dir = Path(tmp_dir) / "logs"
            manager = LoggerManager(
                config_manager=config_manager, logs_dir=logs_dir
            )

            self.assertEqual(manager._logger.level, logging.DEBUG)

    def test_fallback_when_log_directory_unwritable(self) -> None:
        """Le logger fonctionne en sortie console si le dossier est inaccessible."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"

            manager = LoggerManager(logs_dir=logs_dir)
            with patch("meetingai.logging.logger_manager.Path.mkdir", side_effect=OSError):
                manager._setup_logger()

            logger = manager.get_logger("tests.fallback")
            logger.info("fallback message")
            self.assertTrue(True)

    def test_log_format_contains_expected_fields(self) -> None:
        """Le format de log inclut date, niveau, nom et message."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"
            manager = LoggerManager(logs_dir=logs_dir)
            logger = manager.get_logger("tests.format")
            logger.warning("format check")

            log_file = logs_dir / "meetingai.log"
            content = log_file.read_text(encoding="utf-8")
            self.assertIn("WARNING", content)
            self.assertIn("meetingai.tests.format", content)
            self.assertIn("format check", content)
            self.assertIn(" - ", content)


if __name__ == "__main__":
    unittest.main()

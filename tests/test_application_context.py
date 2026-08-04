"""Tests du contexte applicatif de MeetingAI."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from meetingai.config.config_manager import ConfigManager
from meetingai.controllers.runtime_controller import RuntimeController
from meetingai.controllers.transcription_controller import (
    TranscriptionController,
)
from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.services.media_service import MediaService


class TestApplicationContext(unittest.TestCase):
    """Tests du contexte applicatif."""

    @classmethod
    def setUpClass(cls) -> None:
        """Crée l'application Qt unique si nécessaire."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Réinitialise les singletons et prépare un répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._config_path = Path(self._temp_dir.name) / "config.json"
        self._logs_dir = Path(self._temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Réinitialise les singletons et nettoie le répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        self._temp_dir.cleanup()

    def test_creates_config_manager(self) -> None:
        """Le contexte crée une instance de ConfigManager."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(context.config, ConfigManager)

    def test_creates_logger_manager(self) -> None:
        """Le contexte crée une instance de LoggerManager."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(context.logger, LoggerManager)

    def test_creates_service_registry(self) -> None:
        """Le contexte crée une instance de ServiceRegistry."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(context.service_registry, ServiceRegistry)

    def test_creates_action_manager(self) -> None:
        """Le contexte crée une instance de ActionManager."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(context.action_manager, ActionManager)

    def test_registers_components_in_service_registry(self) -> None:
        """Les composants centraux sont enregistrés dans ServiceRegistry."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIs(
            context.service_registry.get("config_manager"),
            context.config,
        )
        self.assertIs(
            context.service_registry.get("logger_manager"),
            context.logger,
        )
        self.assertIs(
            context.service_registry.get("action_manager"),
            context.action_manager,
        )

    def test_context_exposes_single_instances(self) -> None:
        """Le contexte expose toujours les mêmes instances de ses composants."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIs(context.config, context.config)
        self.assertIs(context.logger, context.logger)
        self.assertIs(context.service_registry, context.service_registry)
        self.assertIs(context.action_manager, context.action_manager)

    def test_get_service_uses_registry(self) -> None:
        """``get_service`` retourne un service enregistré."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIs(context.get_service("config_manager"), context.config)

    def test_creates_media_service(self) -> None:
        """Le contexte crée une instance de MediaService."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(context.media_service, MediaService)

    def test_registers_media_service_in_service_registry(self) -> None:
        """MediaService est enregistré dans ServiceRegistry."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIs(
            context.service_registry.get("media_service"),
            context.media_service,
        )

    def test_creates_transcription_controller(self) -> None:
        """Le contexte crée un TranscriptionController."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(
            context.transcription_controller, TranscriptionController
        )

    def test_registers_transcription_controller_in_service_registry(self) -> None:
        """TranscriptionController est enregistré dans ServiceRegistry."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIs(
            context.service_registry.get("transcription_controller"),
            context.transcription_controller,
        )

    def test_creates_runtime_controller(self) -> None:
        """Le contexte crée un RuntimeController."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIsInstance(context.runtime_controller, RuntimeController)

    def test_registers_runtime_controller_in_service_registry(self) -> None:
        """RuntimeController est enregistré dans ServiceRegistry."""
        context = ApplicationContext(config_path=self._config_path)

        self.assertIs(
            context.service_registry.get("runtime_controller"),
            context.runtime_controller,
        )


if __name__ == "__main__":
    unittest.main()

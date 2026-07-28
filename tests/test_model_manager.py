"""Tests du gestionnaire générique de modèles IA."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.ai_model import AIModel, ModelStatus
from meetingai.services.media_service import MediaService
from meetingai.services.model_manager import ModelManager


class TestAIModel(unittest.TestCase):
    """Tests du modèle AIModel."""

    def test_create_model(self) -> None:
        """Un AIModel peut être instancié avec tous les champs."""
        model = AIModel(
            id="whisper-small",
            display_name="Whisper Small",
            family="speech_to_text",
            version="1.0.0",
            size_bytes=466_000_000,
            language="multilingual",
            status=ModelStatus.INSTALLED,
            install_path="models/whisper-small",
        )

        self.assertEqual(model.id, "whisper-small")
        self.assertEqual(model.status, ModelStatus.INSTALLED)


class TestModelManager(unittest.TestCase):
    """Tests du gestionnaire de modèles."""

    def setUp(self) -> None:
        """Réinitialise le singleton avant chaque test."""
        ModelManager._reset_instance()
        self.manager = ModelManager()

    def tearDown(self) -> None:
        """Réinitialise le singleton après chaque test."""
        ModelManager._reset_instance()

    def _sample_model(self, model_id: str, family: str, status: ModelStatus) -> AIModel:
        """Crée un modèle factice."""
        return AIModel(
            id=model_id,
            display_name=model_id,
            family=family,
            version="1.0",
            size_bytes=100,
            language="fr",
            status=status,
        )

    def test_register_and_get(self) -> None:
        """Un modèle peut être enregistré puis récupéré."""
        model = self._sample_model("m1", "speech_to_text", ModelStatus.INSTALLED)
        self.manager.register(model)

        self.assertIs(self.manager.get("m1"), model)

    def test_get_missing_model_raises_key_error(self) -> None:
        """La récupération d'un modèle inexistant lève KeyError."""
        with self.assertRaises(KeyError):
            self.manager.get("missing")

    def test_list_models_sorted(self) -> None:
        """La liste des modèles est triée par identifiant."""
        b = self._sample_model("b", "speech_to_text", ModelStatus.INSTALLED)
        a = self._sample_model("a", "speech_to_text", ModelStatus.NOT_INSTALLED)
        self.manager.register(b)
        self.manager.register(a)

        models = self.manager.list_models()

        self.assertEqual(models, [a, b])

    def test_filter_by_family(self) -> None:
        """Les modèles peuvent être filtrés par famille."""
        stt = self._sample_model("stt", "speech_to_text", ModelStatus.INSTALLED)
        summary = self._sample_model("summary", "summary", ModelStatus.INSTALLED)
        self.manager.register(stt)
        self.manager.register(summary)

        speech_models = self.manager.list_by_family("speech_to_text")

        self.assertEqual(speech_models, [stt])

    def test_is_installed(self) -> None:
        """is_installed retourne True pour un modèle installé."""
        installed = self._sample_model("installed", "speech_to_text", ModelStatus.INSTALLED)
        not_installed = self._sample_model(
            "not_installed", "speech_to_text", ModelStatus.NOT_INSTALLED
        )
        self.manager.register(installed)
        self.manager.register(not_installed)

        self.assertTrue(self.manager.is_installed("installed"))
        self.assertFalse(self.manager.is_installed("not_installed"))

    def test_is_installed_with_update_available(self) -> None:
        """Un modèle avec mise à jour disponible est considéré installé."""
        model = self._sample_model("update", "speech_to_text", ModelStatus.UPDATE_AVAILABLE)
        self.manager.register(model)

        self.assertTrue(self.manager.is_installed("update"))

    def test_unregister_model(self) -> None:
        """Un modèle peut être retiré du registre."""
        model = self._sample_model("m", "speech_to_text", ModelStatus.INSTALLED)
        self.manager.register(model)

        self.manager.unregister("m")

        self.assertFalse(any(m.id == "m" for m in self.manager.list_models()))

    def test_clear_models(self) -> None:
        """Tous les modèles peuvent être retirés."""
        self.manager.register(self._sample_model("m1", "speech_to_text", ModelStatus.INSTALLED))
        self.manager.register(self._sample_model("m2", "summary", ModelStatus.INSTALLED))

        self.manager.clear()

        self.assertEqual(self.manager.list_models(), [])

    def test_singleton(self) -> None:
        """ModelManager est un singleton."""
        first = ModelManager()
        second = ModelManager()
        self.assertIs(first, second)


class TestModelManagerIntegration(unittest.TestCase):
    """Tests d'intégration avec ApplicationContext."""

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
        ModelManager._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._config_path = Path(self._temp_dir.name) / "config.json"
        self._logs_dir = Path(self._temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Réinitialise les singletons et nettoie le répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        ModelManager._reset_instance()
        self._temp_dir.cleanup()

    def test_model_manager_registered_in_service_registry(self) -> None:
        """ApplicationContext crée et enregistre ModelManager."""
        context = ApplicationContext(
            config_path=self._config_path,
            logs_dir=self._logs_dir,
        )

        self.assertIsInstance(context.model_manager, ModelManager)
        self.assertIs(
            context.service_registry.get("model_manager"),
            context.model_manager,
        )


if __name__ == "__main__":
    unittest.main()

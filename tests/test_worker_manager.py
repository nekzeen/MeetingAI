"""Tests de l'infrastructure des Workers."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.core.task import Task
from meetingai.core.worker import Worker
from meetingai.core.worker_manager import WorkerManager
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.services.media_service import MediaService


class TestWorker(unittest.TestCase):
    """Tests de la classe Worker."""

    def test_worker_creation(self) -> None:
        """Un Worker encapsule une tâche, une cible et ses arguments."""
        task = Task(name="transcription")
        target = lambda x: x  # noqa: E731

        worker = Worker(task=task, target=target, args=("hello",), kwargs={"y": 1})

        self.assertIs(worker.task, task)
        self.assertIs(worker.target, target)
        self.assertEqual(worker.args, ("hello",))
        self.assertEqual(worker.kwargs, {"y": 1})


class TestWorkerManager(unittest.TestCase):
    """Tests du gestionnaire de Workers."""

    def setUp(self) -> None:
        """Réinitialise le singleton avant chaque test."""
        WorkerManager._reset_instance()
        self.manager = WorkerManager()

    def tearDown(self) -> None:
        """Réinitialise le singleton après chaque test."""
        WorkerManager._reset_instance()

    def _build_worker(self, name: str = "job") -> Worker:
        """Crée un Worker factice."""
        task = Task(name=name)
        return Worker(task=task, target=lambda: None)

    def test_register_and_get(self) -> None:
        """Un Worker peut être enregistré puis récupéré."""
        worker = self._build_worker()
        self.manager.register(worker)

        self.assertIs(self.manager.get(worker.task.id), worker)

    def test_get_missing_worker_raises_key_error(self) -> None:
        """La récupération d'un Worker inexistant lève KeyError."""
        missing_id = Task(name="missing").id
        with self.assertRaises(KeyError):
            self.manager.get(missing_id)

    def test_list_workers_sorted_by_creation(self) -> None:
        """La liste des Workers est triée par date de création."""
        first = self._build_worker("first")
        second = self._build_worker("second")
        self.manager.register(second)
        self.manager.register(first)

        workers = self.manager.list_workers()

        self.assertEqual(workers, [first, second])

    def test_unregister_worker(self) -> None:
        """Un Worker peut être retiré du registre."""
        worker = self._build_worker()
        self.manager.register(worker)

        self.manager.unregister(worker.task.id)

        self.assertEqual(self.manager.list_workers(), [])

    def test_unregister_missing_worker_raises_key_error(self) -> None:
        """La suppression d'un Worker inexistant lève KeyError."""
        with self.assertRaises(KeyError):
            self.manager.unregister(Task(name="missing").id)

    def test_clear_workers(self) -> None:
        """Tous les Workers peuvent être retirés."""
        self.manager.register(self._build_worker("a"))
        self.manager.register(self._build_worker("b"))

        self.manager.clear()

        self.assertEqual(self.manager.list_workers(), [])

    def test_singleton(self) -> None:
        """WorkerManager est un singleton."""
        first = WorkerManager()
        second = WorkerManager()
        self.assertIs(first, second)


class TestWorkerManagerIntegration(unittest.TestCase):
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
        WorkerManager._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._config_path = Path(self._temp_dir.name) / "config.json"
        self._logs_dir = Path(self._temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Réinitialise les singletons et nettoie le répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        WorkerManager._reset_instance()
        self._temp_dir.cleanup()

    def test_worker_manager_registered_in_service_registry(self) -> None:
        """ApplicationContext crée et enregistre WorkerManager."""
        context = ApplicationContext(
            config_path=self._config_path,
            logs_dir=self._logs_dir,
        )

        self.assertIsInstance(context.worker_manager, WorkerManager)
        self.assertIs(
            context.service_registry.get("worker_manager"),
            context.worker_manager,
        )


if __name__ == "__main__":
    unittest.main()

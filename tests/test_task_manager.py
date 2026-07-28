"""Tests de l'infrastructure des tâches asynchrones."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from meetingai.core.application_context import ApplicationContext
from meetingai.core.service_registry import ServiceRegistry
from meetingai.core.task import Task, TaskStatus
from meetingai.core.task_manager import TaskManager
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.services.media_service import MediaService


class TestTask(unittest.TestCase):
    """Tests du modèle Task."""

    def test_task_default_state(self) -> None:
        """Une tâche nouvellement créée est en attente avec une progression nulle."""
        task = Task(name="transcription")

        self.assertEqual(task.name, "transcription")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.progress, 0)
        self.assertIsNone(task.finished_at)
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)

    def test_task_uuid_is_unique(self) -> None:
        """Chaque tâche possède un identifiant unique."""
        first = Task(name="first")
        second = Task(name="second")

        self.assertNotEqual(first.id, second.id)

    def test_update_progress_clamps_values(self) -> None:
        """La progression est bornée entre 0 et 100."""
        task = Task(name="test")

        task.update_progress(150)
        self.assertEqual(task.progress, 100)

        task.update_progress(-10)
        self.assertEqual(task.progress, 0)


class TestTaskManager(unittest.TestCase):
    """Tests du gestionnaire de tâches."""

    def setUp(self) -> None:
        """Réinitialise le singleton avant chaque test."""
        TaskManager._reset_instance()
        self.manager = TaskManager()

    def tearDown(self) -> None:
        """Réinitialise le singleton après chaque test."""
        TaskManager._reset_instance()

    def test_singleton_returns_same_instance(self) -> None:
        """TaskManager garantit une unique instance."""
        first = TaskManager()
        second = TaskManager()
        self.assertIs(first, second)

    def test_create_task_registers_it(self) -> None:
        """La création d'une tâche l'enregistre automatiquement."""
        task = self.manager.create_task("transcription")

        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIs(self.manager.get(task.id), task)

    def test_register_task(self) -> None:
        """Une tâche peut être enregistrée manuellement."""
        task = Task(name="manual")

        self.manager.register(task)

        self.assertIs(self.manager.get(task.id), task)

    def test_get_missing_task_raises_key_error(self) -> None:
        """La récupération d'une tâche inexistante lève KeyError."""
        with self.assertRaises(KeyError):
            self.manager.get(Task(name="missing").id)

    def test_list_tasks_sorted_by_creation(self) -> None:
        """La liste des tâches est triée par date de création."""
        first = self.manager.create_task("first")
        second = self.manager.create_task("second")

        tasks = self.manager.list_tasks()

        self.assertEqual(tasks, [first, second])

    def test_delete_task(self) -> None:
        """Une tâche peut être supprimée."""
        task = self.manager.create_task("to_delete")

        self.manager.delete(task.id)

        self.assertFalse(any(t.id == task.id for t in self.manager.list_tasks()))

    def test_delete_missing_task_raises_key_error(self) -> None:
        """La suppression d'une tâche inexistante lève KeyError."""
        with self.assertRaises(KeyError):
            self.manager.delete(Task(name="missing").id)

    def test_clear_removes_all_tasks(self) -> None:
        """Le nettoyage supprime toutes les tâches."""
        self.manager.create_task("first")
        self.manager.create_task("second")

        self.manager.clear()

        self.assertEqual(self.manager.list_tasks(), [])


class TestTaskManagerIntegration(unittest.TestCase):
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
        TaskManager._reset_instance()
        self._temp_dir = tempfile.TemporaryDirectory()
        self._config_path = Path(self._temp_dir.name) / "config.json"
        self._logs_dir = Path(self._temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Réinitialise les singletons et nettoie le répertoire temporaire."""
        LoggerManager._reset_instance()
        ServiceRegistry._reset_instance()
        ActionManager._reset_instance()
        MediaService._reset_instance()
        TaskManager._reset_instance()
        self._temp_dir.cleanup()

    def test_task_manager_registered_in_service_registry(self) -> None:
        """ApplicationContext crée et enregistre TaskManager."""
        context = ApplicationContext(
            config_path=self._config_path,
            logs_dir=self._logs_dir,
        )

        self.assertIsInstance(context.task_manager, TaskManager)
        self.assertIs(
            context.service_registry.get("task_manager"),
            context.task_manager,
        )


if __name__ == "__main__":
    unittest.main()

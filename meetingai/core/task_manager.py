"""Gestionnaire central des tâches asynchrones de MeetingAI."""

from __future__ import annotations

import uuid
from typing import ClassVar

from meetingai.core.task import Task, TaskStatus


class TaskManager:
    """Registre et suit les tâches longues de l'application.

    Cette classe suit le pattern singleton afin de garantir un point central
    de suivi des tâches (transcription, IA, export, conversion audio,
    indexation). Elle ne réalise aucune exécution : elle prépare
    l'infrastructure et sera connectée à un moteur d'exécution dans une
    future mission.
    """

    _instance: ClassVar[TaskManager | None] = None
    _initialized: ClassVar[bool] = False

    def __new__(cls) -> TaskManager:
        """Retourne l'instance unique du gestionnaire de tâches."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise le registre des tâches si nécessaire."""
        if TaskManager._initialized:
            return
        TaskManager._initialized = True
        self._tasks: dict[uuid.UUID, Task] = {}

    def create_task(self, name: str) -> Task:
        """Crée et enregistre une nouvelle tâche.

        Args:
            name: Nom décrivant la tâche.

        Returns:
            La tâche nouvellement créée.
        """
        task = Task(name=name)
        self.register(task)
        return task

    def register(self, task: Task) -> None:
        """Enregistre une tâche dans le gestionnaire.

        Args:
            task: Tâche à enregistrer.
        """
        self._tasks[task.id] = task

    def get(self, task_id: uuid.UUID) -> Task:
        """Retourne la tâche correspondant à l'identifiant.

        Args:
            task_id: Identifiant UUID de la tâche.

        Returns:
            La tâche demandée.

        Raises:
            KeyError: Si la tâche n'est pas enregistrée.
        """
        if task_id not in self._tasks:
            raise KeyError(f"Tâche non enregistrée : {task_id}")
        return self._tasks[task_id]

    def list_tasks(self) -> list[Task]:
        """Retourne la liste de toutes les tâches enregistrées.

        Returns:
            Liste des tâches, triée par date de création.
        """
        return sorted(self._tasks.values(), key=lambda task: task.created_at)

    def delete(self, task_id: uuid.UUID) -> None:
        """Supprime une tâche terminée du gestionnaire.

        Args:
            task_id: Identifiant UUID de la tâche.

        Raises:
            KeyError: Si la tâche n'est pas enregistrée.
        """
        if task_id not in self._tasks:
            raise KeyError(f"Tâche non enregistrée : {task_id}")
        del self._tasks[task_id]

    def clear(self) -> None:
        """Supprime toutes les tâches du gestionnaire."""
        self._tasks.clear()

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise le singleton. Réservé aux tests."""
        cls._instance = None
        cls._initialized = False

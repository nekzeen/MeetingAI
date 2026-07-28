"""Gestionnaire central des Workers de MeetingAI."""

from __future__ import annotations

import uuid
from typing import ClassVar

from typing import Any

from meetingai.core.worker import Worker


class WorkerManager:
    """Registre central des unités de travail de l'application.

    Cette classe suit le pattern singleton afin de garantir un point d'accès
    unique aux Workers. Elle ne réalise aucune exécution parallèle : elle
    prépare simplement l'infrastructure qui sera connectée à un moteur
    d'exécution (basé sur ``QThread`` par exemple) dans une future mission.
    """

    _instance: ClassVar[WorkerManager | None] = None
    _initialized: ClassVar[bool] = False

    def __new__(cls) -> WorkerManager:
        """Retourne l'instance unique du gestionnaire de Workers."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise le registre des Workers si nécessaire."""
        if WorkerManager._initialized:
            return
        WorkerManager._initialized = True
        self._workers: dict[uuid.UUID, Worker] = {}

    def register(self, worker: Any) -> None:
        """Enregistre un Worker dans le gestionnaire.

        Args:
            worker: Worker à enregistrer. Doit posséder un attribut ``task``
                avec un ``id``.
        """
        self._workers[worker.task.id] = worker

    def get(self, worker_id: uuid.UUID) -> Worker:
        """Retourne le Worker correspondant à l'identifiant de tâche.

        Args:
            worker_id: Identifiant de la tâche associée au Worker.

        Returns:
            Le Worker demandé.

        Raises:
            KeyError: Si le Worker n'est pas enregistré.
        """
        if worker_id not in self._workers:
            raise KeyError(f"Worker non enregistré : {worker_id}")
        return self._workers[worker_id]

    def list_workers(self) -> list[Any]:
        """Retourne la liste de tous les Workers enregistrés.

        Returns:
            Liste des Workers, triée par date de création de leur tâche.
        """
        return sorted(
            self._workers.values(),
            key=lambda worker: worker.task.created_at,
        )

    def unregister(self, worker_id: uuid.UUID) -> None:
        """Supprime un Worker du registre.

        Args:
            worker_id: Identifiant de la tâche associée au Worker.

        Raises:
            KeyError: Si le Worker n'est pas enregistré.
        """
        if worker_id not in self._workers:
            raise KeyError(f"Worker non enregistré : {worker_id}")
        del self._workers[worker_id]

    def clear(self) -> None:
        """Supprime tous les Workers du registre."""
        self._workers.clear()

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise le singleton. Réservé aux tests."""
        cls._instance = None
        cls._initialized = False

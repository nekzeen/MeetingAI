"""Modèle de tâche asynchrone pour MeetingAI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """États possibles d'une tâche."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Représente une unité de travail exécutée de manière asynchrone.

    Une tâche est créée avec un identifiant unique et un état initial
    ``PENDING``. Les champs ``finished_at``, ``result`` et ``error`` sont
    renseignés au fur et à mesure de l'avancement de la tâche par le moteur
    d'exécution qui lui sera associé ultérieurement.

    Attributes:
        id: Identifiant unique de la tâche.
        name: Nom décrivant la tâche.
        status: État courant de la tâche.
        progress: Progression entière entre 0 et 100.
        created_at: Date et heure de création.
        finished_at: Date et heure de fin, le cas échéant.
        result: Résultat de la tâche, si terminée avec succès.
        error: Message d'erreur, si la tâche a échoué.
    """

    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: TaskStatus = field(default=TaskStatus.PENDING)
    progress: int = field(default=0)
    created_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = field(default=None)
    result: Any = field(default=None)
    error: str | None = field(default=None)

    def update_progress(self, value: int) -> None:
        """Met à jour la progression de la tâche.

        Args:
            value: Nouvelle valeur de progression entre 0 et 100.
        """
        self.progress = max(0, min(100, value))

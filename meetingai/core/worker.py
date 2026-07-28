"""Représentation d'une unité de travail exécutable."""

from dataclasses import dataclass, field
from typing import Any, Callable

from meetingai.core.task import Task


@dataclass
class Worker:
    """Encapsule une tâche et la fonction qui doit l'exécuter.

    Le ``Worker`` est une simple unité exécutable : il associe une ``Task``
    (cycle de vie, progression, résultat) à une fonction callable ainsi qu'à
    ses arguments. Il ne réalise aucune exécution ni aucune gestion de
    thread.

    Attributes:
        task: Tâche associée au Worker.
        target: Fonction à exécuter.
        args: Arguments positionnels à passer à ``target``.
        kwargs: Arguments nommés à passer à ``target``.
    """

    task: Task
    target: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)

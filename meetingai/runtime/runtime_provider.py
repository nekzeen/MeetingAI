"""Contrat commun des providers Runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class RuntimeProvider(ABC):
    """Interface d'un provider capable de diagnostiquer et réparer une
    dépendance d'exécution.

    Les implémentations concrètes représenteront par exemple :

    - le runtime Python et ses packages installés ;
    - les drivers CUDA/cuDNN ;
    - les modèles de transcription présents localement ;
    - les dépendances d'export PDF/DOCX.

    Toutes les méthodes restent synchrones. L'asynchronisme éventuel sera géré
    par les couches supérieures (contrôleurs/workers).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Retourne le nom unique du provider."""

    @property
    @abstractmethod
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la liste des capacités couvertes par ce provider."""

    @abstractmethod
    def status(self) -> RuntimeStatus:
        """Évalue rapidement l'état du provider."""

    @abstractmethod
    def diagnose(self) -> RuntimeReport:
        """Effectue un diagnostic détaillé et retourne un rapport."""

    @abstractmethod
    def can_install(self) -> bool:
        """Indique si le provider peut installer ou réparer sa dépendance."""

    @abstractmethod
    def install(self) -> RuntimeReport:
        """Tente d'installer ou de réparer la dépendance.

        Returns:
            Rapport décrivant le résultat de l'opération.
        """

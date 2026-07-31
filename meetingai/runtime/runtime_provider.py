"""Contrat commun des providers Runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
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

    def suggested_actions(self, report: RuntimeReport) -> list[RuntimeAction]:
        """Retourne les actions suggérées à partir d'un rapport.

        L'implémentation par défaut propose une action générique selon l'état du
        provider (installation, réparation, réessai). Les providers spécifiques
        peuvent surcharger cette méthode pour proposer des actions plus fines.

        Args:
            report: Rapport de diagnostic du provider.

        Returns:
            Liste des actions recommandées.
        """
        actions: list[RuntimeAction] = []
        if report.status == RuntimeStatus.HEALTHY:
            return actions

        if report.status in (RuntimeStatus.MISSING, RuntimeStatus.DEGRADED):
            actions.append(
                RuntimeAction(
                    action_type=RuntimeActionType.INSTALL_PACKAGE,
                    provider_name=self.name,
                    message=f"Installer ou réparer la dépendance '{self.name}'.",
                    description="L'installation automatique est proposée si le provider la supporte.",
                    available=self.can_install(),
                    requires_user=True,
                    parameters={"can_install": self.can_install()},
                )
            )

        if report.status == RuntimeStatus.ERROR:
            actions.append(
                RuntimeAction(
                    action_type=RuntimeActionType.RETRY,
                    provider_name=self.name,
                    message=f"Réessayer le diagnostic pour '{self.name}'.",
                    description="Une erreur transitoire a été détectée ; réessayer peut résoudre le problème.",
                    available=True,
                    requires_user=True,
                )
            )

        if report.status == RuntimeStatus.UNKNOWN:
            actions.append(
                RuntimeAction(
                    action_type=RuntimeActionType.CONFIGURE,
                    provider_name=self.name,
                    message=f"Vérifier la configuration de '{self.name}'.",
                    description="L'état du provider est inconnu ; vérifier la configuration manuellement.",
                    available=False,
                    requires_user=True,
                )
            )

        return actions

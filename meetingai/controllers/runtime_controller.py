"""Contrôleur d'orchestration du Runtime pour l'interface graphique."""

from __future__ import annotations

from meetingai.runtime.runtime_action import RuntimeAction
from meetingai.runtime.runtime_assistant import RuntimeAssistant
from meetingai.runtime.runtime_factory import create_runtime_manager
from meetingai.runtime.runtime_guard import RuntimeGuard, RuntimeGuardResult
from meetingai.runtime.runtime_manager import RuntimeManager
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class RuntimeController:
    """Contrôleur exposant l'état du Runtime et les vérifications de garde.

    Cette couche évite à l'interface graphique de manipuler directement les
    providers. Elle délègue l'intégralité de la logique au ``RuntimeManager``,
    ``RuntimeAssistant`` et ``RuntimeGuard``.

    Args:
        manager: Gestionnaire Runtime. S'il est absent, un manager par défaut
            est créé.
    """

    def __init__(
        self,
        manager: RuntimeManager | None = None,
    ) -> None:
        """Initialise le contrôleur avec un manager Runtime."""
        self._manager = manager or create_runtime_manager()
        self._assistant = RuntimeAssistant(self._manager)
        self._guard = RuntimeGuard(self._assistant)

    @property
    def manager(self) -> RuntimeManager:
        """Retourne le gestionnaire Runtime."""
        return self._manager

    @property
    def assistant(self) -> RuntimeAssistant:
        """Retourne l'assistant Runtime."""
        return self._assistant

    @property
    def guard(self) -> RuntimeGuard:
        """Retourne le garde Runtime."""
        return self._guard

    def status(self) -> RuntimeStatus:
        """Retourne l'état global du Runtime."""
        return self._manager.status()

    def reports(self) -> list[RuntimeReport]:
        """Exécute le diagnostic complet et retourne les rapports."""
        return self._manager.report()

    def actions(self) -> list[RuntimeAction]:
        """Retourne les actions recommandées pour l'environnement actuel."""
        return self._assistant.analyze()

    def is_ready(self) -> bool:
        """Indique si l'environnement est pleinement opérationnel."""
        return self._assistant.is_ready()

    def refresh(self) -> tuple[RuntimeStatus, list[RuntimeReport], list[RuntimeAction]]:
        """Rafraîchit l'état, les rapports et les actions recommandées."""
        return self.status(), self.reports(), self.actions()

    def report_for(self, provider_name: str) -> RuntimeReport | None:
        """Diagnostique un provider donné par son nom.

        Args:
            provider_name: Nom unique du provider à diagnostiquer.

        Returns:
            Rapport du provider, ou ``None`` s'il n'est pas enregistré.
        """
        for provider in self._manager.providers:
            if provider.name == provider_name:
                return provider.diagnose()
        return None

    def install(self, provider_name: str) -> RuntimeReport:
        """Lance l'installation d'un provider donné par son nom.

        Args:
            provider_name: Nom unique du provider à installer.

        Returns:
            Rapport décrivant le résultat de l'installation.
        """
        for provider in self._manager.providers:
            if provider.name == provider_name:
                return provider.install()
        return RuntimeReport(
            provider_name=provider_name,
            status=RuntimeStatus.ERROR,
            message=f"Provider '{provider_name}' introuvable.",
        )

    def check_transcription(self) -> RuntimeGuardResult:
        """Vérifie les prérequis pour une transcription."""
        return self._guard.check_transcription()

    def check_summary(self) -> RuntimeGuardResult:
        """Vérifie les prérequis pour un résumé."""
        return self._guard.check_summary()

    def check_pipeline(self) -> RuntimeGuardResult:
        """Vérifie les prérequis pour un pipeline complet."""
        return self._guard.check_pipeline()

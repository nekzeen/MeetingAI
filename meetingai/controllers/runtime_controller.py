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

    def start_server(self, provider_name: str) -> RuntimeReport:
        """Lance le serveur d'un provider donné par son nom.

        Args:
            provider_name: Nom unique du provider dont le serveur doit être
                démarré.

        Returns:
            Rapport décrivant le résultat de l'opération.
        """
        for provider in self._manager.providers:
            if provider.name == provider_name:
                if not callable(getattr(provider, "start_server", None)):
                    return RuntimeReport(
                        provider_name=provider_name,
                        status=RuntimeStatus.ERROR,
                        message=(
                            f"Le provider '{provider_name}' ne supporte pas "
                            "le démarrage d'un serveur."
                        ),
                    )
                return provider.start_server()
        return RuntimeReport(
            provider_name=provider_name,
            status=RuntimeStatus.ERROR,
            message=f"Provider '{provider_name}' introuvable.",
        )

    def _report_method_not_supported(
        self,
        provider_name: str,
        operation: str,
    ) -> RuntimeReport:
        """Retourne un rapport d'erreur pour une opération non supportée."""
        return RuntimeReport(
            provider_name=provider_name,
            status=RuntimeStatus.ERROR,
            message=(
                f"Le provider '{provider_name}' ne supporte pas "
                f"l'opération '{operation}'."
            ),
        )

    def install_model(self, provider_name: str, model_name: str) -> RuntimeReport:
        """Installe un modèle donné pour un provider donné."""
        for provider in self._manager.providers:
            if provider.name == provider_name:
                if not callable(getattr(provider, "install_model", None)):
                    return self._report_method_not_supported(
                        provider_name, "install_model"
                    )
                return provider.install_model(model_name)
        return RuntimeReport(
            provider_name=provider_name,
            status=RuntimeStatus.ERROR,
            message=f"Provider '{provider_name}' introuvable.",
        )

    def remove_model(self, provider_name: str, model_name: str) -> RuntimeReport:
        """Supprime un modèle donné pour un provider donné."""
        for provider in self._manager.providers:
            if provider.name == provider_name:
                if not callable(getattr(provider, "remove_model", None)):
                    return self._report_method_not_supported(
                        provider_name, "remove_model"
                    )
                return provider.remove_model(model_name)
        return RuntimeReport(
            provider_name=provider_name,
            status=RuntimeStatus.ERROR,
            message=f"Provider '{provider_name}' introuvable.",
        )

    def set_model(self, provider_name: str, model_name: str) -> RuntimeReport:
        """Sélectionne un modèle comme modèle actif pour un provider donné."""
        for provider in self._manager.providers:
            if provider.name == provider_name:
                if not callable(getattr(provider, "set_model", None)):
                    return self._report_method_not_supported(
                        provider_name, "set_model"
                    )
                return provider.set_model(model_name)
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

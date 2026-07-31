"""Gestionnaire central des providers Runtime."""

from __future__ import annotations

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class RuntimeManager:
    """Regroupe les providers Runtime et expose l'état global de l'exécution.

    Le manager ne contient aucune logique métier spécifique à une dépendance :
    il délègue chaque opération aux providers enregistrés et agrège les
    résultats.

    Args:
        providers: Providers initialement enregistrés.
    """

    def __init__(
        self,
        providers: list[RuntimeProvider] | None = None,
    ) -> None:
        """Initialise le gestionnaire avec la liste optionnelle de providers."""
        self._providers: list[RuntimeProvider] = list(providers) if providers else []

    def register(self, provider: RuntimeProvider) -> None:
        """Enregistre un nouveau provider."""
        self._providers.append(provider)

    @property
    def providers(self) -> list[RuntimeProvider]:
        """Retourne la liste des providers enregistrés."""
        return self._providers.copy()

    def status(self) -> RuntimeStatus:
        """Retourne l'état global, correspondant au plus critique des providers.

        Si aucun provider n'est enregistré, retourne ``RuntimeStatus.UNKNOWN``.
        """
        if not self._providers:
            return RuntimeStatus.UNKNOWN
        return max(
            (provider.status() for provider in self._providers),
            key=lambda status: status.severity,
        )

    def report(self) -> list[RuntimeReport]:
        """Exécute un diagnostic complet de tous les providers."""
        return [provider.diagnose() for provider in self._providers]

    def providers_for(
        self,
        capability: RuntimeCapability,
    ) -> list[RuntimeProvider]:
        """Retourne les providers déclarant la capacité demandée."""
        return [
            provider
            for provider in self._providers
            if capability in provider.capabilities
        ]

    def ensure(self, capability: RuntimeCapability) -> list[RuntimeReport]:
        """Tente d'assurer qu'au moins un provider sain couvre la capacité.

        Pour chaque provider concerné, si son état n'est pas sain et qu'il
        supporte l'installation, ``install()`` est appelé. Les rapports de
        diagnostic avant et après installation sont agrégés.
        """
        reports: list[RuntimeReport] = []
        for provider in self.providers_for(capability):
            report = provider.diagnose()
            reports.append(report)
            if report.status != RuntimeStatus.HEALTHY and provider.can_install():
                reports.append(provider.install())
        return reports

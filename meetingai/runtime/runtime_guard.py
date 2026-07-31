"""Couche de garde Runtime pour vérifier les prérequis avant exécution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_assistant import RuntimeAssistant
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


@dataclass(frozen=True)
class RuntimeGuardResult:
    """Résultat d'une vérification de garde Runtime.

    Attributes:
        allowed: Indique si l'opération peut être lancée.
        reports: Rapports de diagnostic collectés pour les capacités requises.
        actions: Actions recommandées si la vérification a échoué.
        details: Informations complémentaires (capacités requises, etc.).
    """

    allowed: bool
    reports: list[RuntimeReport] = field(default_factory=list)
    actions: list[RuntimeAction] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class RuntimeGuard:
    """Vérifie qu'une opération métier peut s'exécuter dans l'environnement actuel.

    ``RuntimeGuard`` interroge l'assistant pour diagnostiquer les providers
    couvrant les capacités requises. Si au moins un provider sain existe pour
    chaque capacité, l'opération est autorisée. Sinon, les rapports et actions
    recommandées sont retournés sans déclencher le traitement.

    Args:
        assistant: Assistant Runtime initialisé avec le manager à utiliser.
    """

    def __init__(self, assistant: RuntimeAssistant) -> None:
        """Initialise le garde avec un assistant."""
        self._assistant = assistant

    def _check_capability(
        self,
        capability: RuntimeCapability,
    ) -> tuple[bool, list[RuntimeReport], list[RuntimeAction]]:
        """Vérifie une capacité et retourne son état, rapports et actions."""
        providers = self._assistant.manager.providers_for(capability)
        if not providers:
            return (
                False,
                [],
                [
                    RuntimeAction(
                        action_type=RuntimeActionType.CONFIGURE,
                        provider_name="",
                        message=f"Aucun provider enregistré pour '{capability.value}'.",
                        description="Vérifiez la configuration du Runtime.",
                        available=False,
                        requires_user=True,
                    )
                ],
            )

        reports: list[RuntimeReport] = []
        actions: list[RuntimeAction] = []
        capability_healthy = False

        for provider in providers:
            report = provider.diagnose()
            reports.append(report)
            if report.status == RuntimeStatus.HEALTHY:
                capability_healthy = True
            else:
                actions.extend(provider.suggested_actions(report))

        return capability_healthy, reports, actions if not capability_healthy else []

    def check(self, *capabilities: RuntimeCapability) -> RuntimeGuardResult:
        """Vérifie que toutes les capacités demandées sont disponibles.

        Args:
            capabilities: Capacités requises pour l'opération.

        Returns:
            Résultat indiquant si l'exécution est autorisée et les actions
            suggérées le cas échéant.
        """
        all_allowed = True
        all_reports: list[RuntimeReport] = []
        all_actions: list[RuntimeAction] = []

        for capability in capabilities:
            allowed, reports, actions = self._check_capability(capability)
            all_reports.extend(reports)
            if not allowed:
                all_allowed = False
                all_actions.extend(actions)

        return RuntimeGuardResult(
            allowed=all_allowed,
            reports=all_reports,
            actions=all_actions,
            details={"required_capabilities": [c.value for c in capabilities]},
        )

    def check_transcription(self) -> RuntimeGuardResult:
        """Vérifie les prérequis pour une transcription."""
        return self.check(
            RuntimeCapability.SPEECH_TO_TEXT,
            RuntimeCapability.MEDIA_PROCESSING,
        )

    def check_summary(self) -> RuntimeGuardResult:
        """Vérifie les prérequis pour un résumé."""
        return self.check(RuntimeCapability.SUMMARIZATION)

    def check_pipeline(self) -> RuntimeGuardResult:
        """Vérifie les prérequis pour un pipeline complet (transcription + résumé)."""
        return self.check(
            RuntimeCapability.SPEECH_TO_TEXT,
            RuntimeCapability.MEDIA_PROCESSING,
            RuntimeCapability.SUMMARIZATION,
        )

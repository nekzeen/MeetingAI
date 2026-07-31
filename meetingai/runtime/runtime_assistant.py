"""Assistant Runtime pour guider l'utilisateur lors du premier lancement."""

from __future__ import annotations

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_manager import RuntimeManager
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class RuntimeAssistant:
    """Transforme les rapports Runtime en actions utilisateur suggérées.

    L'assistant ne déclenche pas d'opérations lourdes de lui-même : il collecte
    les diagnostics, demande aux providers leurs actions recommandées et les
    expose sous une forme exploitable par l'interface de première utilisation ou
    les outils de maintenance.

    Args:
        manager: Gestionnaire contenant les providers à analyser.
    """

    def __init__(self, manager: RuntimeManager) -> None:
        """Initialise l'assistant avec un RuntimeManager."""
        self._manager = manager

    def _reports(self) -> list[RuntimeReport]:
        """Exécute le diagnostic complet de tous les providers."""
        return self._manager.report()

    def is_ready(self) -> bool:
        """Indique si l'environnement est pleinement opérationnel."""
        reports = self._reports()
        if not reports:
            return False
        return all(report.status == RuntimeStatus.HEALTHY for report in reports)

    def analyze(self) -> list[RuntimeAction]:
        """Retourne l'ensemble des actions suggérées après diagnostic.

        Returns:
            Liste ordonnée des actions recommandées pour chaque provider.
        """
        actions: list[RuntimeAction] = []
        for provider in self._manager.providers:
            report = provider.diagnose()
            actions.extend(provider.suggested_actions(report))
        return actions

    def first_run_guide(self) -> list[RuntimeAction]:
        """Retourne les actions prioritaires pour le premier lancement.

        Filtre les actions proposées pour ne conserver que celles qui peuvent
        faire avancer l'installation (installation, téléchargement, démarrage
        d'un serveur ou réparation).

        Returns:
            Liste des actions à présenter à l'utilisateur.
        """
        return [
            action
            for action in self.analyze()
            if action.action_type
            in {
                RuntimeActionType.INSTALL_PACKAGE,
                RuntimeActionType.DOWNLOAD_MODEL,
                RuntimeActionType.START_SERVER,
                RuntimeActionType.REPAIR,
                RuntimeActionType.CONFIGURE,
                RuntimeActionType.RETRY,
            }
        ]

    def actions_for(self, provider_name: str) -> list[RuntimeAction]:
        """Retourne les actions d'un provider nommé."""
        return [
            action
            for action in self.analyze()
            if action.provider_name == provider_name
        ]

    def top_action(self) -> RuntimeAction | None:
        """Retourne l'action la plus prioritaire ou ``None`` si tout est sain."""
        actions = self.analyze()
        if not actions:
            return None
        return actions[0]

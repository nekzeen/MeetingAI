"""Tests de l'assistant Runtime et des actions recommandées."""

import unittest
from typing import Any
from unittest.mock import MagicMock

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_assistant import RuntimeAssistant
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_manager import RuntimeManager
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class FakeProvider(RuntimeProvider):
    """Provider factice pour les tests."""

    def __init__(
        self,
        name: str,
        status: RuntimeStatus,
        can_install: bool = False,
    ) -> None:
        """Initialise le provider factice."""
        self._name = name
        self._status = status
        self._can_install = can_install

    @property
    def name(self) -> str:
        """Nom du provider."""
        return self._name

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Capacités du provider."""
        return []

    def status(self) -> RuntimeStatus:
        """État du provider."""
        return self._status

    def diagnose(self) -> RuntimeReport:
        """Diagnostic du provider."""
        return RuntimeReport(
            provider_name=self._name,
            status=self._status,
            message=f"{self._name} diagnostic.",
            details={},
        )

    def can_install(self) -> bool:
        """Indique si l'installation est supportée."""
        return self._can_install

    def install(self) -> RuntimeReport:
        """Tente d'installer le provider."""
        return RuntimeReport(
            provider_name=self._name,
            status=self._status,
            message="Installation.",
            details={},
        )


class TestRuntimeAction(unittest.TestCase):
    """Tests du modèle d'action."""

    def test_action_creation(self) -> None:
        """RuntimeAction stocke ses champs."""
        action = RuntimeAction(
            action_type=RuntimeActionType.INSTALL_PACKAGE,
            provider_name="python",
            message="Installer Python.",
            description="Python 3.12 est requis.",
            available=False,
            requires_user=True,
            parameters={"version": "3.12"},
        )

        self.assertEqual(action.action_type, RuntimeActionType.INSTALL_PACKAGE)
        self.assertEqual(action.provider_name, "python")
        self.assertEqual(action.message, "Installer Python.")
        self.assertFalse(action.available)


class TestRuntimeProviderSuggestedActions(unittest.TestCase):
    """Tests des suggestions par défaut du provider."""

    def test_healthy_returns_empty_list(self) -> None:
        """Aucune action n'est proposée si le provider est sain."""
        provider = FakeProvider("python", RuntimeStatus.HEALTHY)
        report = provider.diagnose()

        self.assertEqual(provider.suggested_actions(report), [])

    def test_missing_with_install_support(self) -> None:
        """MISSING + can_install propose une action disponible."""
        provider = FakeProvider("ffmpeg", RuntimeStatus.MISSING, can_install=True)
        report = provider.diagnose()
        actions = provider.suggested_actions(report)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].action_type, RuntimeActionType.INSTALL_PACKAGE)
        self.assertEqual(actions[0].available, True)
        self.assertEqual(actions[0].parameters["can_install"], True)

    def test_missing_without_install_support(self) -> None:
        """MISSING sans can_install propose une action indisponible."""
        provider = FakeProvider("python", RuntimeStatus.MISSING, can_install=False)
        report = provider.diagnose()
        actions = provider.suggested_actions(report)

        self.assertEqual(actions[0].available, False)

    def test_degraded_suggests_install(self) -> None:
        """DEGRADED propose une action de réparation/installation."""
        provider = FakeProvider("cuda", RuntimeStatus.DEGRADED, can_install=True)
        report = provider.diagnose()
        actions = provider.suggested_actions(report)

        self.assertEqual(actions[0].action_type, RuntimeActionType.INSTALL_PACKAGE)

    def test_error_suggests_retry(self) -> None:
        """ERROR propose une action de réessai."""
        provider = FakeProvider("cuda", RuntimeStatus.ERROR)
        report = provider.diagnose()
        actions = provider.suggested_actions(report)

        self.assertEqual(actions[0].action_type, RuntimeActionType.RETRY)

    def test_unknown_suggests_configure(self) -> None:
        """UNKNOWN propose une action de configuration."""
        provider = FakeProvider("cuda", RuntimeStatus.UNKNOWN)
        report = provider.diagnose()
        actions = provider.suggested_actions(report)

        self.assertEqual(actions[0].action_type, RuntimeActionType.CONFIGURE)
        self.assertFalse(actions[0].available)


class TestRuntimeAssistant(unittest.TestCase):
    """Tests de l'assistant Runtime."""

    def _build_manager(self, providers: list[RuntimeProvider]) -> RuntimeManager:
        """Construit un manager avec les providers fournis."""
        return RuntimeManager(providers)

    def test_is_ready_true_when_all_healthy(self) -> None:
        """is_ready retourne True si tous les providers sont HEALTHY."""
        manager = self._build_manager(
            [
                FakeProvider("a", RuntimeStatus.HEALTHY),
                FakeProvider("b", RuntimeStatus.HEALTHY),
            ]
        )
        assistant = RuntimeAssistant(manager)

        self.assertTrue(assistant.is_ready())

    def test_is_ready_false_when_one_degraded(self) -> None:
        """is_ready retourne False si au moins un provider n'est pas sain."""
        manager = self._build_manager(
            [
                FakeProvider("a", RuntimeStatus.HEALTHY),
                FakeProvider("b", RuntimeStatus.DEGRADED),
            ]
        )
        assistant = RuntimeAssistant(manager)

        self.assertFalse(assistant.is_ready())

    def test_analyze_returns_actions(self) -> None:
        """analyze agrège les actions de tous les providers."""
        manager = self._build_manager(
            [
                FakeProvider("whisper", RuntimeStatus.MISSING, can_install=False),
                FakeProvider("ollama", RuntimeStatus.DEGRADED, can_install=True),
            ]
        )
        assistant = RuntimeAssistant(manager)

        actions = assistant.analyze()

        self.assertEqual(len(actions), 2)
        self.assertEqual({a.provider_name for a in actions}, {"whisper", "ollama"})

    def test_first_run_guide_filters_actions(self) -> None:
        """first_run_guide ignore les actions de type NONE."""
        manager = self._build_manager(
            [
                FakeProvider("a", RuntimeStatus.HEALTHY),
                FakeProvider("b", RuntimeStatus.MISSING, can_install=True),
            ]
        )
        assistant = RuntimeAssistant(manager)

        guide = assistant.first_run_guide()

        self.assertEqual(len(guide), 1)
        self.assertEqual(guide[0].action_type, RuntimeActionType.INSTALL_PACKAGE)

    def test_actions_for_provider(self) -> None:
        """actions_for filtre par nom de provider."""
        manager = self._build_manager(
            [
                FakeProvider("whisper", RuntimeStatus.MISSING, can_install=True),
                FakeProvider("ollama", RuntimeStatus.MISSING, can_install=True),
            ]
        )
        assistant = RuntimeAssistant(manager)

        actions = assistant.actions_for("whisper")

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].provider_name, "whisper")

    def test_top_action_returns_first(self) -> None:
        """top_action retourne la première action suggérée."""
        manager = self._build_manager(
            [FakeProvider("whisper", RuntimeStatus.MISSING, can_install=True)]
        )
        assistant = RuntimeAssistant(manager)

        top = assistant.top_action()

        self.assertIsNotNone(top)
        self.assertEqual(top.action_type, RuntimeActionType.INSTALL_PACKAGE)

    def test_top_action_returns_none_when_ready(self) -> None:
        """top_action retourne None si l'environnement est sain."""
        manager = self._build_manager(
            [FakeProvider("whisper", RuntimeStatus.HEALTHY)]
        )
        assistant = RuntimeAssistant(manager)

        self.assertIsNone(assistant.top_action())

    def test_manager_without_providers_is_not_ready(self) -> None:
        """Un manager vide est considéré comme non prêt."""
        assistant = RuntimeAssistant(RuntimeManager())

        self.assertFalse(assistant.is_ready())


if __name__ == "__main__":
    unittest.main()

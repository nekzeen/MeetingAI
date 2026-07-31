"""Tests du garde Runtime et de ses vérifications de prérequis."""

import unittest

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_assistant import RuntimeAssistant
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_guard import RuntimeGuard, RuntimeGuardResult
from meetingai.runtime.runtime_manager import RuntimeManager
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class FakeProvider(RuntimeProvider):
    """Provider factice pour les tests de garde."""

    def __init__(
        self,
        name: str,
        capabilities: list[RuntimeCapability],
        status: RuntimeStatus,
    ) -> None:
        """Initialise le provider factice."""
        self._name = name
        self._capabilities = capabilities
        self._status = status

    @property
    def name(self) -> str:
        """Nom du provider."""
        return self._name

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Capacités du provider."""
        return self._capabilities

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
        """Installation non supportée par défaut."""
        return False

    def install(self) -> RuntimeReport:
        """Installation factice."""
        return RuntimeReport(
            provider_name=self._name,
            status=self._status,
            message="Installation.",
            details={},
        )

    def suggested_actions(self, report: RuntimeReport) -> list[RuntimeAction]:
        """Retourne une action factice si le provider n'est pas sain."""
        if report.status == RuntimeStatus.HEALTHY:
            return []
        return [
            RuntimeAction(
                action_type=RuntimeActionType.RETRY,
                provider_name=self._name,
                message=f"Action {self._name}",
                description="Action proposée par le provider factice.",
                available=True,
                requires_user=True,
            )
        ]


class TestRuntimeGuardResult(unittest.TestCase):
    """Tests du résultat de garde."""

    def test_default_result(self) -> None:
        """RuntimeGuardResult stocke allowed, reports et actions."""
        result = RuntimeGuardResult(allowed=True)

        self.assertTrue(result.allowed)
        self.assertEqual(result.reports, [])
        self.assertEqual(result.actions, [])


class TestRuntimeGuard(unittest.TestCase):
    """Tests du garde Runtime."""

    def _guard(
        self,
        providers: list[RuntimeProvider],
    ) -> RuntimeGuard:
        """Construit un RuntimeGuard à partir de providers factices."""
        manager = RuntimeManager(providers)
        assistant = RuntimeAssistant(manager)
        return RuntimeGuard(assistant)

    def test_check_allows_when_healthy(self) -> None:
        """La vérification autorise l'exécution si le provider est sain."""
        guard = self._guard(
            [
                FakeProvider(
                    "whisper",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.HEALTHY,
                )
            ]
        )

        result = guard.check(RuntimeCapability.SPEECH_TO_TEXT)

        self.assertTrue(result.allowed)
        self.assertEqual(len(result.reports), 1)
        self.assertEqual(result.actions, [])

    def test_check_blocks_when_missing(self) -> None:
        """La vérification bloque et retourne des actions si le provider est manquant."""
        guard = self._guard(
            [
                FakeProvider(
                    "whisper",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.MISSING,
                )
            ]
        )

        result = guard.check(RuntimeCapability.SPEECH_TO_TEXT)

        self.assertFalse(result.allowed)
        self.assertEqual(len(result.reports), 1)
        self.assertTrue(len(result.actions) > 0)

    def test_check_allows_when_one_provider_healthy(self) -> None:
        """Une capacité est satisfaite si au moins un provider est sain."""
        guard = self._guard(
            [
                FakeProvider(
                    "whisper",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.MISSING,
                ),
                FakeProvider(
                    "backup",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.HEALTHY,
                ),
            ]
        )

        result = guard.check(RuntimeCapability.SPEECH_TO_TEXT)

        self.assertTrue(result.allowed)

    def test_check_transcription_requires_multiple_capabilities(self) -> None:
        """check_transcription requiert la transcription et le traitement média."""
        guard = self._guard(
            [
                FakeProvider(
                    "whisper",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.HEALTHY,
                ),
                FakeProvider(
                    "ffmpeg",
                    [RuntimeCapability.MEDIA_PROCESSING],
                    RuntimeStatus.HEALTHY,
                ),
            ]
        )

        result = guard.check_transcription()

        self.assertTrue(result.allowed)
        self.assertIn("speech_to_text", result.details["required_capabilities"])
        self.assertIn("media_processing", result.details["required_capabilities"])

    def test_check_transcription_blocks_if_media_missing(self) -> None:
        """check_transcription bloque si un prérequis média est manquant."""
        guard = self._guard(
            [
                FakeProvider(
                    "whisper",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.HEALTHY,
                ),
                FakeProvider(
                    "ffmpeg",
                    [RuntimeCapability.MEDIA_PROCESSING],
                    RuntimeStatus.MISSING,
                ),
            ]
        )

        result = guard.check_transcription()

        self.assertFalse(result.allowed)
        self.assertTrue(len(result.actions) > 0)

    def test_check_summary(self) -> None:
        """check_summary requiert la capacité de summarization."""
        guard = self._guard(
            [
                FakeProvider(
                    "ollama",
                    [RuntimeCapability.SUMMARIZATION],
                    RuntimeStatus.HEALTHY,
                )
            ]
        )

        result = guard.check_summary()

        self.assertTrue(result.allowed)

    def test_check_pipeline_requires_all(self) -> None:
        """check_pipeline bloge si une capacité est manquante."""
        guard = self._guard(
            [
                FakeProvider(
                    "whisper",
                    [RuntimeCapability.SPEECH_TO_TEXT],
                    RuntimeStatus.HEALTHY,
                ),
                FakeProvider(
                    "ffmpeg",
                    [RuntimeCapability.MEDIA_PROCESSING],
                    RuntimeStatus.HEALTHY,
                ),
                FakeProvider(
                    "ollama",
                    [RuntimeCapability.SUMMARIZATION],
                    RuntimeStatus.MISSING,
                ),
            ]
        )

        result = guard.check_pipeline()

        self.assertFalse(result.allowed)
        self.assertIn("summarization", result.details["required_capabilities"])

    def test_check_unknown_capability_returns_action(self) -> None:
        """Une capacité sans provider retourne une action CONFIGURE."""
        guard = self._guard([])

        result = guard.check(RuntimeCapability.PDF_EXPORT)

        self.assertFalse(result.allowed)
        self.assertEqual(result.actions[0].action_type, RuntimeActionType.CONFIGURE)


if __name__ == "__main__":
    unittest.main()

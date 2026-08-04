"""Tests du contrôleur Runtime."""

import unittest
from unittest.mock import MagicMock

from meetingai.controllers.runtime_controller import RuntimeController
from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_assistant import RuntimeAssistant
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_guard import RuntimeGuard
from meetingai.runtime.runtime_manager import RuntimeManager
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class FakeProvider(RuntimeProvider):
    """Provider factice pour les tests du contrôleur."""

    def __init__(
        self,
        name: str,
        status: RuntimeStatus,
        capabilities: list[RuntimeCapability] | None = None,
    ) -> None:
        """Initialise le provider factice."""
        self._name = name
        self._status = status
        self._capabilities = capabilities or [RuntimeCapability.SPEECH_TO_TEXT]

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
        """Installation supportée si le provider est manquant."""
        return self._status != RuntimeStatus.HEALTHY

    def install(self) -> RuntimeReport:
        """Installation factice."""
        return RuntimeReport(
            provider_name=self._name,
            status=self._status,
            message="Installation.",
            details={},
        )

    def suggested_actions(self, report: RuntimeReport) -> list[RuntimeAction]:
        """Actions proposées par le provider."""
        if report.status == RuntimeStatus.HEALTHY:
            return []
        return [
            RuntimeAction(
                action_type=RuntimeActionType.RETRY,
                provider_name=self._name,
                message=f"Réessayer {self._name}",
                description="Action proposée.",
                available=True,
                requires_user=True,
            )
        ]


class TestRuntimeController(unittest.TestCase):
    """Tests du contrôleur Runtime."""

    def _controller(
        self,
        providers: list[RuntimeProvider] | None = None,
    ) -> RuntimeController:
        """Construit un contrôleur avec les providers fournis."""
        return RuntimeController(RuntimeManager(providers or []))

    def test_exposes_assistant(self) -> None:
        """Le contrôleur expose l'assistant Runtime."""
        controller = self._controller()

        self.assertIsInstance(controller.assistant, RuntimeAssistant)

    def test_exposes_guard(self) -> None:
        """Le contrôleur expose le garde Runtime."""
        controller = self._controller()

        self.assertIsInstance(controller.guard, RuntimeGuard)

    def test_status_returns_manager_status(self) -> None:
        """status() retourne l'état du manager."""
        controller = self._controller([FakeProvider("whisper", RuntimeStatus.HEALTHY)])

        self.assertEqual(controller.status(), RuntimeStatus.HEALTHY)

    def test_reports_returns_diagnoses(self) -> None:
        """reports() exécute le diagnostic des providers."""
        controller = self._controller([FakeProvider("whisper", RuntimeStatus.HEALTHY)])

        reports = controller.reports()

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].provider_name, "whisper")

    def test_actions_returns_assistant_actions(self) -> None:
        """actions() retourne les actions suggérées par l'assistant."""
        controller = self._controller(
            [FakeProvider("whisper", RuntimeStatus.MISSING)]
        )

        actions = controller.actions()

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].provider_name, "whisper")

    def test_is_ready_true_when_all_healthy(self) -> None:
        """is_ready() retourne True si tous les providers sont sains."""
        controller = self._controller(
            [FakeProvider("whisper", RuntimeStatus.HEALTHY)]
        )

        self.assertTrue(controller.is_ready())

    def test_is_ready_false_when_missing(self) -> None:
        """is_ready() retourne False si un provider est manquant."""
        controller = self._controller(
            [FakeProvider("whisper", RuntimeStatus.MISSING)]
        )

        self.assertFalse(controller.is_ready())

    def test_refresh_returns_status_reports_and_actions(self) -> None:
        """refresh() retourne l'état, les rapports et les actions."""
        controller = self._controller(
            [FakeProvider("whisper", RuntimeStatus.MISSING)]
        )

        status, reports, actions = controller.refresh()

        self.assertEqual(status, RuntimeStatus.MISSING)
        self.assertEqual(len(reports), 1)
        self.assertEqual(len(actions), 1)

    def test_check_transcription_uses_guard(self) -> None:
        """check_transcription() interroge le garde."""
        stt = FakeProvider(
            "whisper",
            RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.SPEECH_TO_TEXT],
        )
        media = FakeProvider(
            "ffmpeg",
            RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.MEDIA_PROCESSING],
        )
        controller = self._controller([stt, media])

        result = controller.check_transcription()

        self.assertIsNotNone(result)
        self.assertTrue(result.allowed)

    def test_check_summary_uses_guard(self) -> None:
        """check_summary() interroge le garde."""
        provider = FakeProvider(
            "ollama",
            RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.SUMMARIZATION],
        )
        controller = self._controller([provider])

        result = controller.check_summary()

        self.assertIsNotNone(result)
        self.assertTrue(result.allowed)

    def test_check_pipeline_uses_guard(self) -> None:
        """check_pipeline() interroge le garde."""
        stt = FakeProvider(
            "whisper",
            RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.SPEECH_TO_TEXT],
        )
        summary = FakeProvider(
            "ollama",
            RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.SUMMARIZATION],
        )
        media = FakeProvider(
            "ffmpeg",
            RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.MEDIA_PROCESSING],
        )

        controller = self._controller([stt, media, summary])

        result = controller.check_pipeline()

        self.assertIsNotNone(result)
        self.assertTrue(result.allowed)

    def test_report_for_returns_matching_provider_diagnose(self) -> None:
        """report_for retourne le diagnostic du provider demandé."""
        provider = MagicMock()
        provider.name = "whisper"
        provider.diagnose.return_value = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.HEALTHY,
            message="ok",
        )
        controller = self._controller([provider])

        report = controller.report_for("whisper")

        provider.diagnose.assert_called_once()
        self.assertEqual(report.provider_name, "whisper")

    def test_report_for_returns_none_for_unknown_provider(self) -> None:
        """report_for retourne None si le provider est inconnu."""
        controller = self._controller([])

        self.assertIsNone(controller.report_for("whisper"))

    def test_install_calls_matching_provider_install(self) -> None:
        """install délègue au provider portant le nom donné."""
        provider = MagicMock()
        provider.name = "whisper"
        provider.install.return_value = RuntimeReport(
            provider_name="whisper",
            status=RuntimeStatus.HEALTHY,
            message="installed",
        )
        controller = self._controller([provider])

        report = controller.install("whisper")

        provider.install.assert_called_once()
        self.assertEqual(report.status, RuntimeStatus.HEALTHY)

    def test_install_returns_error_for_unknown_provider(self) -> None:
        """install retourne une erreur si le provider est inconnu."""
        controller = self._controller([])

        report = controller.install("whisper")

        self.assertEqual(report.status, RuntimeStatus.ERROR)
        self.assertIn("introuvable", report.message)


if __name__ == "__main__":
    unittest.main()

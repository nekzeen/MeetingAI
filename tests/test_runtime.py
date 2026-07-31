"""Tests de l'architecture Runtime."""

from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import MagicMock

from meetingai.runtime import (
    RuntimeCapability,
    RuntimeManager,
    RuntimeProvider,
    RuntimeReport,
    RuntimeStatus,
)


class TestRuntimeStatus(unittest.TestCase):
    """Tests des états du Runtime."""

    def test_status_ordering(self) -> None:
        """Les états sont ordonnés par sévérité croissante."""
        self.assertLess(RuntimeStatus.HEALTHY, RuntimeStatus.DEGRADED)
        self.assertLess(RuntimeStatus.DEGRADED, RuntimeStatus.MISSING)
        self.assertLess(RuntimeStatus.MISSING, RuntimeStatus.ERROR)
        self.assertLess(RuntimeStatus.ERROR, RuntimeStatus.UNKNOWN)

    def test_max_returns_most_severe(self) -> None:
        """max() retourne l'état le plus critique."""
        statuses = [
            RuntimeStatus.HEALTHY,
            RuntimeStatus.DEGRADED,
            RuntimeStatus.ERROR,
        ]
        worst = max(statuses, key=lambda status: status.severity)
        self.assertIs(worst, RuntimeStatus.ERROR)


class TestRuntimeReport(unittest.TestCase):
    """Tests des rapports Runtime."""

    def test_report_fields(self) -> None:
        """RuntimeReport expose les champs attendus."""
        report = RuntimeReport(
            provider_name="python",
            status=RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.SPEECH_TO_TEXT],
            message="OK",
            details={"version": "3.12"},
        )
        self.assertEqual(report.provider_name, "python")
        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.capabilities, [RuntimeCapability.SPEECH_TO_TEXT])
        self.assertEqual(report.message, "OK")
        self.assertEqual(report.details, {"version": "3.12"})

    def test_report_is_immutable(self) -> None:
        """Les rapports sont figés après création."""
        report = RuntimeReport(
            provider_name="python",
            status=RuntimeStatus.HEALTHY,
        )
        with self.assertRaises(AttributeError):
            report.status = RuntimeStatus.ERROR  # type: ignore[misc]


class TestRuntimeManager(unittest.TestCase):
    """Tests du gestionnaire de providers Runtime."""

    def _build_provider(
        self,
        name: str,
        status: RuntimeStatus,
        capabilities: list[RuntimeCapability],
        can_install: bool = False,
        install_report: RuntimeReport | None = None,
    ) -> MagicMock:
        """Crée un provider simulé conforme à RuntimeProvider."""
        provider = MagicMock(spec=RuntimeProvider)
        provider.name = name
        provider.capabilities = capabilities
        provider.status.return_value = status
        report = RuntimeReport(
            provider_name=name,
            status=status,
            capabilities=capabilities,
        )
        provider.diagnose.return_value = report
        provider.can_install.return_value = can_install
        provider.install.return_value = install_report or report
        return provider

    def test_status_unknown_when_empty(self) -> None:
        """Un manager sans provider retourne UNKNOWN."""
        manager = RuntimeManager()
        self.assertEqual(manager.status(), RuntimeStatus.UNKNOWN)

    def test_status_aggregates_worst_state(self) -> None:
        """L'état global correspond au provider le plus critique."""
        healthy = self._build_provider(
            "python",
            RuntimeStatus.HEALTHY,
            [RuntimeCapability.SUMMARIZATION],
        )
        missing = self._build_provider(
            "cuda",
            RuntimeStatus.MISSING,
            [RuntimeCapability.GPU_ACCELERATION],
        )
        manager = RuntimeManager([healthy, missing])

        self.assertEqual(manager.status(), RuntimeStatus.MISSING)

    def test_report_collects_provider_reports(self) -> None:
        """report() agrège les diagnostics de tous les providers."""
        provider = self._build_provider(
            "python",
            RuntimeStatus.HEALTHY,
            [RuntimeCapability.SPEECH_TO_TEXT],
        )
        manager = RuntimeManager([provider])

        reports = manager.report()

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].provider_name, "python")
        provider.diagnose.assert_called_once()

    def test_providers_for_filters_by_capability(self) -> None:
        """providers_for retourne uniquement les providers concernés."""
        stt = self._build_provider(
            "stt",
            RuntimeStatus.HEALTHY,
            [RuntimeCapability.SPEECH_TO_TEXT],
        )
        gpu = self._build_provider(
            "gpu",
            RuntimeStatus.MISSING,
            [RuntimeCapability.GPU_ACCELERATION],
        )
        manager = RuntimeManager([stt, gpu])

        providers = manager.providers_for(RuntimeCapability.GPU_ACCELERATION)

        self.assertEqual(providers, [gpu])

    def test_healthy_provider_is_not_reinstalled(self) -> None:
        """ensure n'installe pas un provider déjà sain."""
        provider = self._build_provider(
            "stt",
            RuntimeStatus.HEALTHY,
            [RuntimeCapability.SPEECH_TO_TEXT],
            can_install=True,
        )
        manager = RuntimeManager([provider])

        reports = manager.ensure(RuntimeCapability.SPEECH_TO_TEXT)

        self.assertEqual(len(reports), 1)
        provider.install.assert_not_called()

    def test_unhealthy_provider_is_installed_when_possible(self) -> None:
        """ensure installe un provider manquant s'il le supporte."""
        install_report = RuntimeReport(
            provider_name="stt",
            status=RuntimeStatus.HEALTHY,
            capabilities=[RuntimeCapability.SPEECH_TO_TEXT],
            message="installed",
        )
        provider = self._build_provider(
            "stt",
            RuntimeStatus.MISSING,
            [RuntimeCapability.SPEECH_TO_TEXT],
            can_install=True,
            install_report=install_report,
        )
        manager = RuntimeManager([provider])

        reports = manager.ensure(RuntimeCapability.SPEECH_TO_TEXT)

        self.assertEqual(len(reports), 2)
        provider.install.assert_called_once()
        self.assertEqual(reports[-1].message, "installed")

    def test_register_adds_provider(self) -> None:
        """register ajoute un provider après création du manager."""
        manager = RuntimeManager()
        provider = self._build_provider(
            "stt",
            RuntimeStatus.HEALTHY,
            [RuntimeCapability.SPEECH_TO_TEXT],
        )

        manager.register(provider)

        self.assertEqual(manager.providers, [provider])


class TestRuntimeFactory(unittest.TestCase):
    """Tests de la factory Runtime."""

    def test_create_runtime_manager_registers_all_providers(self) -> None:
        """create_runtime_manager enregistre les providers standard."""
        from meetingai.runtime import create_runtime_manager

        manager = create_runtime_manager()
        names = {provider.name for provider in manager.providers}

        self.assertGreaterEqual(
            names,
            {"python", "ffmpeg", "whisper", "ollama", "cuda"},
        )


class TestRuntimeProviderContract(unittest.TestCase):
    """Tests du contrat RuntimeProvider."""

    def test_abstract_methods(self) -> None:
        """RuntimeProvider ne peut pas être instancié directement."""
        with self.assertRaises(TypeError):
            RuntimeProvider()  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()

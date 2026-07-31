"""Tests du provider de résumé Ollama."""

import unittest
from unittest.mock import MagicMock

from meetingai.runtime.providers.ollama_runtime_provider import (
    OllamaRuntimeProvider,
)
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus
from meetingai.services.summarization.ollama_summarization_service import (
    OllamaSummarizationService,
)
from meetingai.services.summarization.summary_profile import ProfileRegistry
from meetingai.services.summarization.summary_result import SummaryResult


class TestOllamaSummarizationService(unittest.TestCase):
    """Tests du service de résumé Ollama."""

    def _mock_provider(self) -> MagicMock:
        """Crée un provider Ollama simulé."""
        return MagicMock(spec=OllamaRuntimeProvider)

    def _make_report(
        self,
        status: RuntimeStatus,
        message: str = "",
        details: dict | None = None,
    ) -> RuntimeReport:
        """Construit un rapport RuntimeReport."""
        return RuntimeReport(
            provider_name="ollama",
            status=status,
            message=message,
            details=details or {},
        )

    def test_name_returns_ollama(self) -> None:
        """Le provider s'identifie comme ollama."""
        service = OllamaSummarizationService(runtime_provider=self._mock_provider())

        self.assertEqual(service.name(), "ollama")

    def test_is_available_returns_true_when_healthy(self) -> None:
        """is_available retourne True si le runtime est sain."""
        provider = self._mock_provider()
        provider.status.return_value = RuntimeStatus.HEALTHY
        service = OllamaSummarizationService(runtime_provider=provider)

        self.assertTrue(service.is_available())

    def test_is_available_returns_true_when_degraded(self) -> None:
        """is_available retourne True même si le modèle est manquant."""
        provider = self._mock_provider()
        provider.status.return_value = RuntimeStatus.DEGRADED
        service = OllamaSummarizationService(runtime_provider=provider)

        self.assertTrue(service.is_available())

    def test_is_available_returns_false_when_missing(self) -> None:
        """is_available retourne False si le serveur est manquant."""
        provider = self._mock_provider()
        provider.status.return_value = RuntimeStatus.MISSING
        service = OllamaSummarizationService(runtime_provider=provider)

        self.assertFalse(service.is_available())

    def test_summarize_returns_summary_result(self) -> None:
        """summarize retourne un SummaryResult à partir de la réponse Ollama."""
        provider = self._mock_provider()
        provider.generate.return_value = self._make_report(
            RuntimeStatus.HEALTHY,
            details={"response": "Résumé Ollama."},
        )
        service = OllamaSummarizationService(runtime_provider=provider)
        profile = ProfileRegistry().get("concise")

        result = service.summarize("Texte long à résumer.", profile)

        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.text, "Résumé Ollama.")
        self.assertEqual(result.provider, "ollama")
        provider.generate.assert_called_once()

    def test_summarize_trims_response(self) -> None:
        """summarize nettoie les espaces autour du résumé."""
        provider = self._mock_provider()
        provider.generate.return_value = self._make_report(
            RuntimeStatus.HEALTHY,
            details={"response": "  Résumé nettoyé.  "},
        )
        service = OllamaSummarizationService(runtime_provider=provider)
        profile = ProfileRegistry().get("concise")

        result = service.summarize("Texte.", profile)

        self.assertEqual(result.text, "Résumé nettoyé.")

    def test_summarize_raises_on_error_report(self) -> None:
        """summarize lève une erreur si le rapport retourne un état en échec."""
        provider = self._mock_provider()
        provider.generate.return_value = self._make_report(
            RuntimeStatus.ERROR,
            message="Internal Server Error",
        )
        service = OllamaSummarizationService(runtime_provider=provider)
        profile = ProfileRegistry().get("concise")

        with self.assertRaises(RuntimeError) as context:
            service.summarize("Texte.", profile)

        self.assertIn("Internal Server Error", str(context.exception))

    def test_summarize_raises_on_missing_response_field(self) -> None:
        """summarize lève une erreur si le champ response est absent."""
        provider = self._mock_provider()
        provider.generate.return_value = self._make_report(
            RuntimeStatus.HEALTHY,
            details={"done": True},
        )
        service = OllamaSummarizationService(runtime_provider=provider)
        profile = ProfileRegistry().get("concise")

        with self.assertRaises(RuntimeError):
            service.summarize("Texte.", profile)

    def test_available_models_returns_sorted_names(self) -> None:
        """available_models extrait et trie les noms des modèles."""
        provider = self._mock_provider()
        provider.list_installed_models.return_value = self._make_report(
            RuntimeStatus.HEALTHY,
            details={"models": ["llama3.2", "mistral"]},
        )
        service = OllamaSummarizationService(runtime_provider=provider)

        models = service.available_models()

        self.assertEqual(models, ["llama3.2", "mistral"])

    def test_available_models_returns_empty_list(self) -> None:
        """available_models retourne une liste vide si aucun modèle n'est installé."""
        provider = self._mock_provider()
        provider.list_installed_models.return_value = self._make_report(
            RuntimeStatus.HEALTHY,
            details={"models": []},
        )
        service = OllamaSummarizationService(runtime_provider=provider)

        models = service.available_models()

        self.assertEqual(models, [])

    def test_available_models_raises_when_report_not_healthy(self) -> None:
        """available_models lève une erreur si le rapport n'est pas sain."""
        provider = self._mock_provider()
        provider.list_installed_models.return_value = self._make_report(
            RuntimeStatus.MISSING,
            message="connection refused",
        )
        service = OllamaSummarizationService(runtime_provider=provider)

        with self.assertRaises(RuntimeError) as context:
            service.available_models()

        self.assertIn("connection refused", str(context.exception))


if __name__ == "__main__":
    unittest.main()

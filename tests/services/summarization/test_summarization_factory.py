"""Tests de l'architecture de résumé IA."""

import unittest

from meetingai.services.summarization.fake_summarization_service import (
    FakeSummarizationService,
)
from meetingai.services.summarization.ollama_summarization_service import (
    OllamaSummarizationService,
)
from meetingai.services.summarization.summary_result import SummaryResult
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)
from meetingai.services.summarization.summary_profile import ProfileRegistry
from meetingai.services.summarization.summarization_service import (
    SummarizationService,
)


class TestSummarizationFactory(unittest.TestCase):
    """Tests de la factory de providers de résumé IA."""

    def setUp(self) -> None:
        """Crée une factory fraîche pour chaque test."""
        self.factory = SummarizationFactory()

    def test_fake_provider_is_registered(self) -> None:
        """Le provider ``fake`` est enregistré par défaut."""
        self.assertIn("fake", self.factory.available_providers())

    def test_create_returns_service_instance(self) -> None:
        """create retourne une instance de SummarizationService."""
        service = self.factory.create("fake")

        self.assertIsInstance(service, SummarizationService)

    def test_create_fake_returns_fake_service(self) -> None:
        """create('fake') retourne une instance de FakeSummarizationService."""
        service = self.factory.create("fake")

        self.assertIsInstance(service, FakeSummarizationService)

    def test_ollama_provider_is_registered(self) -> None:
        """Le provider ``ollama`` est enregistré par défaut."""
        self.assertIn("ollama", self.factory.available_providers())

    def test_create_ollama_returns_ollama_service(self) -> None:
        """create('ollama') retourne une instance de OllamaSummarizationService."""
        service = self.factory.create("ollama")

        self.assertIsInstance(service, OllamaSummarizationService)

    def test_create_unknown_provider_raises(self) -> None:
        """create avec un provider inconnu lève ValueError."""
        with self.assertRaises(ValueError) as context:
            self.factory.create("unknown")

        self.assertIn("unknown", str(context.exception))

    def test_register_provider_extends_factory(self) -> None:
        """register_provider permet d'ajouter un nouveau provider."""
        class CustomSummarizationService(SummarizationService):
            def name(self) -> str:
                return "custom"

            def is_available(self) -> bool:
                return True

            def summarize(
                self,
                text: str,
                profile: object,
            ) -> SummaryResult:
                return SummaryResult(text="résumé custom", provider="custom")

            def available_models(self) -> list[str]:
                return []

        self.factory.register_provider("custom", CustomSummarizationService)

        self.assertIn("custom", self.factory.available_providers())
        service = self.factory.create("custom")
        self.assertIsInstance(service, CustomSummarizationService)


class TestFakeSummarizationService(unittest.TestCase):
    """Tests du provider de résumé IA factice."""

    def test_name_returns_fake(self) -> None:
        """Le provider factice s'identifie comme ``fake``."""
        service = FakeSummarizationService()

        self.assertEqual(service.name(), "fake")

    def test_is_available_returns_true(self) -> None:
        """Le provider factice est toujours disponible."""
        service = FakeSummarizationService()

        self.assertTrue(service.is_available())

    def test_summarize_returns_fixed_summary(self) -> None:
        """summarize retourne un résumé fixe lié au profil par défaut."""
        service = FakeSummarizationService()
        profile = ProfileRegistry().get("concise")

        result = service.summarize("Un long texte à résumer.", profile)

        self.assertIsInstance(result, SummaryResult)
        self.assertIn("Ceci est un résumé simulé.", result.text)
        self.assertIn(profile.label, result.text)
        self.assertEqual(result.provider, "fake")

    def test_summarize_changes_text_with_profile(self) -> None:
        """summarize inclut le libellé du profil dans le résumé factice."""
        service = FakeSummarizationService()
        profile = ProfileRegistry().get("key_points")

        result = service.summarize("Texte.", profile)

        self.assertIn(profile.label, result.text)


if __name__ == "__main__":
    unittest.main()

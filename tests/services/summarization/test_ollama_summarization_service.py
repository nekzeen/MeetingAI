"""Tests du provider de résumé Ollama."""

import json
import unittest
from unittest.mock import patch

from meetingai.services.summarization.ollama_summarization_service import (
    OllamaSummarizationService,
)
from meetingai.services.summarization.summary_result import SummaryResult


class _MockHTTPResponse:
    """Réponse HTTP factice pour urllib.request.urlopen."""

    def __init__(self, payload: bytes, status: int = 200) -> None:
        """Initialise la réponse avec un corps et un statut."""
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        """Retourne le corps de la réponse."""
        return self._payload

    def __enter__(self) -> "_MockHTTPResponse":
        """Support du context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Ne fait rien."""


class TestOllamaSummarizationService(unittest.TestCase):
    """Tests du service de résumé Ollama."""

    def test_name_returns_ollama(self) -> None:
        """Le provider s'identifie comme ollama."""
        service = OllamaSummarizationService()

        self.assertEqual(service.name(), "ollama")

    def test_is_available_returns_true_when_server_responds(self) -> None:
        """is_available retourne True si le serveur répond."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(b'{"models": []}')

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            self.assertTrue(service.is_available())

    def test_is_available_returns_false_when_server_fails(self) -> None:
        """is_available retourne False si le serveur ne répond pas."""
        service = OllamaSummarizationService()

        with patch(
            "meetingai.services.summarization.ollama_summarization_service.urlopen",
            side_effect=Exception("connection refused"),
        ):
            self.assertFalse(service.is_available())

    def test_summarize_returns_summary_result(self) -> None:
        """summarize retourne un SummaryResult à partir de la réponse Ollama."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(
            json.dumps({"response": "Résumé Ollama."}).encode("utf-8")
        )

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            result = service.summarize("Texte long à résumer.")

        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.text, "Résumé Ollama.")
        self.assertEqual(result.provider, "ollama")

    def test_summarize_trims_response(self) -> None:
        """summarize nettoie les espaces autour du résumé."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(
            json.dumps({"response": "  Résumé nettoyé.  "}).encode("utf-8")
        )

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            result = service.summarize("Texte.")

        self.assertEqual(result.text, "Résumé nettoyé.")

    def test_summarize_raises_on_http_error(self) -> None:
        """summarize lève une erreur en cas d'échec HTTP."""
        service = OllamaSummarizationService()

        with patch(
            "meetingai.services.summarization.ollama_summarization_service.urlopen",
            side_effect=Exception("Internal Server Error"),
        ):
            with self.assertRaises(RuntimeError):
                service.summarize("Texte.")

    def test_summarize_raises_on_missing_response_field(self) -> None:
        """summarize lève une erreur si le champ response est absent."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(json.dumps({"done": True}).encode("utf-8"))

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            with self.assertRaises(RuntimeError):
                service.summarize("Texte.")

    def test_summarize_raises_on_invalid_json(self) -> None:
        """summarize lève une erreur si la réponse n'est pas du JSON valide."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(b"not json")

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            with self.assertRaises(RuntimeError):
                service.summarize("Texte.")

    def test_available_models_returns_sorted_names(self) -> None:
        """available_models extrait et trie les noms des modèles."""
        service = OllamaSummarizationService()
        payload = {
            "models": [
                {"name": "llama3.2"},
                {"name": "mistral"},
            ]
        }
        response = _MockHTTPResponse(json.dumps(payload).encode("utf-8"))

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            models = service.available_models()

        self.assertEqual(models, ["llama3.2", "mistral"])

    def test_available_models_returns_empty_list(self) -> None:
        """available_models retourne une liste vide si aucun modèle n'est installé."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(
            json.dumps({"models": []}).encode("utf-8")
        )

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            models = service.available_models()

        self.assertEqual(models, [])

    def test_available_models_raises_when_server_is_down(self) -> None:
        """available_models lève une erreur si le serveur est indisponible."""
        service = OllamaSummarizationService()

        with patch(
            "meetingai.services.summarization.ollama_summarization_service.urlopen",
            side_effect=Exception("connection refused"),
        ):
            with self.assertRaises(RuntimeError):
                service.available_models()

    def test_available_models_raises_on_invalid_json(self) -> None:
        """available_models lève une erreur si la réponse est invalide."""
        service = OllamaSummarizationService()
        response = _MockHTTPResponse(b"not json")

        with patch("meetingai.services.summarization.ollama_summarization_service.urlopen", return_value=response):
            with self.assertRaises(RuntimeError):
                service.available_models()


if __name__ == "__main__":
    unittest.main()

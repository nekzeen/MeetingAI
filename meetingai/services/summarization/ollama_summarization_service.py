"""Provider de résumé IA via Ollama."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen

from meetingai.services.summarization.summary_profile import SummaryProfile
from meetingai.services.summarization.summary_result import SummaryResult
from meetingai.services.summarization.summarization_service import (
    SummarizationService,
)


class OllamaSummarizationService(SummarizationService):
    """Génère un résumé en appelant l'API locale Ollama.

    Args:
        base_url: URL du serveur Ollama.
        model: Nom du modèle à utiliser.
        timeout: Délai d'attente maximal en secondes.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: int = 30,
    ) -> None:
        """Initialise le service Ollama avec ses paramètres de connexion."""
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def name(self) -> str:
        """Retourne le nom du provider."""
        return "ollama"

    def is_available(self) -> bool:
        """Vérifie que le serveur Ollama répond.

        Returns:
            ``True`` si le serveur est joignable, ``False`` sinon.
        """
        try:
            request = Request(
                f"{self._base_url}/api/tags",
                method="GET",
            )
            with urlopen(request, timeout=self._timeout):
                return True
        except Exception:
            return False

    def summarize(
        self,
        text: str,
        profile: SummaryProfile,
    ) -> SummaryResult:
        """Résume le texte fourni via l'API Ollama selon le profil.

        Args:
            text: Texte à résumer.
            profile: Profil de résumé à appliquer.

        Returns:
            Résultat du résumé.

        Raises:
            RuntimeError: Si la requête échoue ou si la réponse est invalide.
        """
        prompt = f"{profile.instruction}\n\n{text}"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        request = Request(
            f"{self._base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Réponse invalide reçue depuis Ollama."
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Échec de la communication avec Ollama : {exc}"
            ) from exc

        summary = data.get("response")
        if summary is None:
            raise RuntimeError("Réponse Ollama inattendue : champ 'response' manquant.")

        return SummaryResult(text=summary.strip(), provider=self.name())

    def available_models(self) -> list[str]:
        """Retourne la liste des modèles installés sur le serveur Ollama.

        Returns:
            Noms des modèles disponibles.

        Raises:
            RuntimeError: Si la requête échoue ou si la réponse est invalide.
        """
        request = Request(
            f"{self._base_url}/api/tags",
            method="GET",
        )

        try:
            with urlopen(request, timeout=self._timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Réponse invalide reçue depuis Ollama."
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Échec de la récupération des modèles Ollama : {exc}"
            ) from exc

        models = data.get("models", [])
        if not isinstance(models, list):
            raise RuntimeError("Réponse Ollama inattendue pour /api/tags.")

        names: list[str] = []
        for model in models:
            if isinstance(model, dict):
                name = model.get("name")
                if name:
                    names.append(str(name))
            elif isinstance(model, str):
                names.append(model)

        return sorted(names)

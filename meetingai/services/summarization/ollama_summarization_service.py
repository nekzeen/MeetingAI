"""Provider de résumé IA via Ollama."""

from __future__ import annotations

from meetingai.runtime.providers.ollama_runtime_provider import (
    OllamaRuntimeProvider,
)
from meetingai.runtime.runtime_status import RuntimeStatus
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
        runtime_provider: OllamaRuntimeProvider | None = None,
    ) -> None:
        """Initialise le service Ollama avec ses paramètres de connexion."""
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._provider = runtime_provider or OllamaRuntimeProvider(
            host=base_url,
            model=model,
            timeout=timeout,
        )

    def name(self) -> str:
        """Retourne le nom du provider."""
        return "ollama"

    def is_available(self) -> bool:
        """Vérifie que le serveur Ollama répond."""
        status = self._provider.status()
        return status in (RuntimeStatus.HEALTHY, RuntimeStatus.DEGRADED)

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
        report = self._provider.generate(prompt, self._model)

        if report.status != RuntimeStatus.HEALTHY:
            raise RuntimeError(f"Échec de la communication avec Ollama : {report.message}")

        summary = report.details.get("response")
        if summary is None:
            raise RuntimeError("Réponse Ollama inattendue : champ 'response' manquant.")

        return SummaryResult(text=str(summary).strip(), provider=self.name())

    def available_models(self) -> list[str]:
        """Retourne la liste des modèles installés sur le serveur Ollama.

        Returns:
            Noms des modèles disponibles.

        Raises:
            RuntimeError: Si la requête échoue ou si la réponse est invalide.
        """
        report = self._provider.list_installed_models()

        if report.status != RuntimeStatus.HEALTHY:
            raise RuntimeError(
                f"Échec de la récupération des modèles Ollama : {report.message}"
            )

        models = report.details.get("models", [])
        if not isinstance(models, list):
            raise RuntimeError("Réponse Ollama inattendue pour /api/tags.")

        return sorted(str(name) for name in models if name)

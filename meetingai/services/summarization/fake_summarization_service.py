"""Provider de résumé IA fictif pour valider l'architecture."""

from __future__ import annotations

from meetingai.services.summarization.summary_result import SummaryResult
from meetingai.services.summarization.summarization_service import (
    SummarizationService,
)


class FakeSummarizationService(SummarizationService):
    """Provider de résumé IA factice retournant un texte fixe."""

    _NAME: str = "fake"
    _FIXED_SUMMARY: str = "Ceci est un résumé simulé."

    def name(self) -> str:
        """Retourne le nom du provider factice."""
        return self._NAME

    def is_available(self) -> bool:
        """Le provider factice est toujours disponible."""
        return True

    def summarize(self, text: str) -> SummaryResult:
        """Retourne un résumé factice.

        Args:
            text: Texte à résumer (ignoré).

        Returns:
            Résultat de résumé factice.
        """
        return SummaryResult(text=self._FIXED_SUMMARY, provider=self._NAME)

    def available_models(self) -> list[str]:
        """Le provider factice n'a pas de modèles."""
        return []

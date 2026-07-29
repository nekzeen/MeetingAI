"""Contrat commun des providers de résumé IA."""

from __future__ import annotations

from abc import ABC, abstractmethod

from meetingai.services.summarization.summary_result import SummaryResult


class SummarizationService(ABC):
    """Interface commune pour les providers de résumé IA.

    Cette classe abstraite permet de changer de provider de résumé IA sans
    impacter le reste de l'application.
    """

    @abstractmethod
    def name(self) -> str:
        """Retourne le nom du provider.

        Returns:
            Nom lisible du provider.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Indique si le provider est utilisable dans l'environnement courant.

        Returns:
            ``True`` si le provider peut être utilisé.
        """

    @abstractmethod
    def summarize(self, text: str) -> SummaryResult:
        """Résume le texte fourni.

        Args:
            text: Texte à résumer.

        Returns:
            Résultat du résumé.
        """

    @abstractmethod
    def available_models(self) -> list[str]:
        """Retourne la liste des modèles utilisables par ce provider.

        Returns:
            Liste des noms de modèles disponibles.
        """

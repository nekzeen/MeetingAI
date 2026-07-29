"""Factory des providers de résumé IA."""

from __future__ import annotations

from meetingai.services.summarization.fake_summarization_service import (
    FakeSummarizationService,
)
from meetingai.services.summarization.summarization_service import (
    SummarizationService,
)


class SummarizationFactory:
    """Crée les instances de ``SummarizationService`` selon le provider.

    Les providers sont enregistrés dans un registre interne. De nouveaux
    providers peuvent être ajoutés via ``register_provider`` sans modifier
    le code existant.
    """

    def __init__(self) -> None:
        """Initialise la factory avec les providers par défaut."""
        self._providers: dict[str, type[SummarizationService]] = {
            "fake": FakeSummarizationService,
        }

    def register_provider(
        self,
        name: str,
        provider_class: type[SummarizationService],
    ) -> None:
        """Enregistre un nouveau provider de résumé IA.

        Args:
            name: Identifiant du provider.
            provider_class: Classe implémentant ``SummarizationService``.
        """
        self._providers[name] = provider_class

    def available_providers(self) -> list[str]:
        """Retourne la liste des providers enregistrés."""
        return sorted(self._providers.keys())

    def create(self, provider_name: str) -> SummarizationService:
        """Instancie le provider demandé.

        Args:
            provider_name: Identifiant du provider.

        Returns:
            Instance du provider de résumé IA.

        Raises:
            ValueError: Si le provider n'est pas enregistré.
        """
        provider_class = self._providers.get(provider_name)
        if provider_class is None:
            raise ValueError(
                f"Provider de résumé IA inconnu : {provider_name}"
            )
        return provider_class()

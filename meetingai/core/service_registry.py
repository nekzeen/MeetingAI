"""Registre central des services de MeetingAI.

Ce module fournit un registre partagé permettant d'enregistrer et de récupérer
les services de l'application sans introduire d'import circulaire ni de
dépendance vers la couche graphique.
"""

from __future__ import annotations

from typing import Any, ClassVar


class ServiceRegistry:
    """Registre centralisé des services de l'application.

    Cette classe suit le pattern singleton afin de garantir un point d'accès
    unique aux services enregistrés. Elle constitue la base de l'injection de
    dépendances utilisée par le cœur de l'application.

    Example:
        >>> registry = ServiceRegistry()
        >>> registry.register("database", db_service)
        >>> registry.get("database")
    """

    _instance: ClassVar[ServiceRegistry | None] = None
    _initialized: ClassVar[bool] = False

    def __new__(cls) -> ServiceRegistry:
        """Retourne l'instance unique du registre."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise le dictionnaire de services si nécessaire."""
        if ServiceRegistry._initialized:
            return
        ServiceRegistry._initialized = True
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Enregistre un service sous le nom indiqué.

        Args:
            name: Nom unique du service.
            service: Instance du service à enregistrer.
        """
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Retourne le service associé au nom demandé.

        Args:
            name: Nom du service à récupérer.

        Returns:
            L'instance du service enregistrée.

        Raises:
            KeyError: Si aucun service n'est enregistré sous ce nom.
        """
        try:
            return self._services[name]
        except KeyError as exc:
            raise KeyError(f"Service non enregistré : {name}") from exc

    def has(self, name: str) -> bool:
        """Indique si un service est enregistré sous le nom indiqué.

        Args:
            name: Nom du service recherché.

        Returns:
            ``True`` si le service existe, ``False`` sinon.
        """
        return name in self._services

    def unregister(self, name: str) -> None:
        """Supprime le service enregistré sous le nom indiqué.

        Args:
            name: Nom du service à supprimer.

        Raises:
            KeyError: Si aucun service n'est enregistré sous ce nom.
        """
        if name not in self._services:
            raise KeyError(f"Service non enregistré : {name}")
        del self._services[name]

    def clear(self) -> None:
        """Supprime tous les services du registre."""
        self._services.clear()

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise le singleton. Réservé aux tests."""
        cls._instance = None
        cls._initialized = False

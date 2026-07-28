"""Gestionnaire générique des modèles IA de MeetingAI."""

from __future__ import annotations

from typing import ClassVar

from meetingai.models.ai_model import AIModel, ModelStatus


class ModelManager:
    """Registre central des modèles IA disponibles et installés.

    Cette classe suit le pattern singleton afin de garantir un point d'accès
    unique aux modèles de l'application. Elle est volontairement indépendante
    de tout moteur IA spécifique : elle manipule uniquement des objets
    ``AIModel`` et ne réalise aucun téléchargement, aucun accès réseau ni
    aucun accès au système de fichiers.

    Elle pourra être utilisée par les différentes familles de modèles :
    transcription, résumé IA, OCR, traduction, etc.
    """

    _instance: ClassVar[ModelManager | None] = None
    _initialized: ClassVar[bool] = False

    def __new__(cls) -> ModelManager:
        """Retourne l'instance unique du gestionnaire de modèles."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise le registre des modèles si nécessaire."""
        if ModelManager._initialized:
            return
        ModelManager._initialized = True
        self._models: dict[str, AIModel] = {}

    def register(self, model: AIModel) -> None:
        """Enregistre ou remplace un modèle dans le gestionnaire.

        Args:
            model: Modèle à enregistrer.
        """
        self._models[model.id] = model

    def get(self, model_id: str) -> AIModel:
        """Retourne le modèle correspondant à l'identifiant.

        Args:
            model_id: Identifiant du modèle.

        Returns:
            Le modèle demandé.

        Raises:
            KeyError: Si le modèle n'est pas enregistré.
        """
        if model_id not in self._models:
            raise KeyError(f"Modèle non enregistré : {model_id}")
        return self._models[model_id]

    def list_models(self) -> list[AIModel]:
        """Retourne la liste de tous les modèles enregistrés.

        Returns:
            Liste des modèles, triée par identifiant.
        """
        return sorted(self._models.values(), key=lambda model: model.id)

    def list_by_family(self, family: str) -> list[AIModel]:
        """Retourne les modèles appartenant à une famille donnée.

        Args:
            family: Famille de modèles recherchée.

        Returns:
            Liste des modèles de cette famille.
        """
        return [
            model
            for model in self.list_models()
            if model.family == family
        ]

    def is_installed(self, model_id: str) -> bool:
        """Indique si un modèle est installé.

        Args:
            model_id: Identifiant du modèle.

        Returns:
            ``True`` si le modèle est enregistré et son statut est
            ``INSTALLED`` ou ``UPDATE_AVAILABLE``.

        Raises:
            KeyError: Si le modèle n'est pas enregistré.
        """
        model = self.get(model_id)
        return model.status in {
            ModelStatus.INSTALLED,
            ModelStatus.UPDATE_AVAILABLE,
        }

    def unregister(self, model_id: str) -> None:
        """Supprime un modèle du registre.

        Cette opération ne supprime aucun fichier sur le disque.

        Args:
            model_id: Identifiant du modèle à supprimer.

        Raises:
            KeyError: Si le modèle n'est pas enregistré.
        """
        if model_id not in self._models:
            raise KeyError(f"Modèle non enregistré : {model_id}")
        del self._models[model_id]

    def clear(self) -> None:
        """Supprime tous les modèles du registre."""
        self._models.clear()

    @classmethod
    def _reset_instance(cls) -> None:
        """Réinitialise le singleton. Réservé aux tests."""
        cls._instance = None
        cls._initialized = False

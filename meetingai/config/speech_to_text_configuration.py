"""Configuration immuable des moteurs Speech-To-Text."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SpeechToTextConfiguration:
    """Paramètres de sélection et d'exécution d'un moteur Speech-To-Text.

    Cette dataclass immutable centralise la configuration sans dépendre d'une
    implémentation concrète. Elle permet de basculer entre les moteurs
    (``fake``, ``faster-whisper``...) uniquement en modifiant la configuration.

    Attributes:
        provider: Identifiant du moteur à utiliser.
        model_name: Nom ou taille du modèle à charger.
        models_directory: Répertoire racine des modèles locaux.
        device: Périphérique d'exécution (``auto``, ``cpu``, ``cuda``).
        compute_type: Type de calcul (``int8``, ``float16``, etc.).
        language: Langue forcée du média, si connue.
    """

    provider: str = "fake"
    model_name: str = "small"
    models_directory: str = "models"
    device: str = "auto"
    compute_type: str = "int8"
    language: str | None = None

    def with_provider(self, provider: str) -> "SpeechToTextConfiguration":
        """Retourne une nouvelle configuration avec le provider modifié."""
        return SpeechToTextConfiguration(
            provider=provider,
            model_name=self.model_name,
            models_directory=self.models_directory,
            device=self.device,
            compute_type=self.compute_type,
            language=self.language,
        )

    def with_options(self, **options: Any) -> "SpeechToTextConfiguration":
        """Retourne une nouvelle configuration avec les options remplacées."""
        current = {
            "provider": self.provider,
            "model_name": self.model_name,
            "models_directory": self.models_directory,
            "device": self.device,
            "compute_type": self.compute_type,
            "language": self.language,
        }
        current.update(options)
        return SpeechToTextConfiguration(**current)

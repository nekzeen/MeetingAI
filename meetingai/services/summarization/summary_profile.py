"""Profils de résumé IA."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SummaryProfile:
    """Définit un profil de résumé.

    Un profil associe une clé technique, un libellé affiché et une
    instruction envoyée au provider pour orienter la génération.
    """

    key: str
    label: str
    instruction: str


class ProfileRegistry:
    """Registre des profils de résumé disponibles."""

    _DEFAULT_PROFILES: tuple[SummaryProfile, ...] = (
        SummaryProfile(
            "concise",
            "Résumé concis",
            "Résume le texte suivant de manière concise en français.",
        ),
        SummaryProfile(
            "meeting_minutes",
            "Compte rendu de réunion",
            (
                "Rédige un compte rendu structuré de la réunion suivante "
                "en français."
            ),
        ),
        SummaryProfile(
            "key_points",
            "Points clés",
            "Extrais les points clés du texte suivant en français.",
        ),
        SummaryProfile(
            "action_items",
            "Actions à entreprendre",
            (
                "Liste les actions à entreprendre mentionnées dans le texte "
                "suivant en français."
            ),
        ),
        SummaryProfile(
            "decisions",
            "Décisions prises",
            (
                "Liste les décisions prises dans le texte suivant en français."
            ),
        ),
    )

    def __init__(self) -> None:
        """Initialise le registre avec les profils par défaut."""
        self._profiles: dict[str, SummaryProfile] = {
            profile.key: profile for profile in self._DEFAULT_PROFILES
        }

    def register(self, profile: SummaryProfile) -> None:
        """Enregistre un nouveau profil.

        Args:
            profile: Profil à ajouter.
        """
        self._profiles[profile.key] = profile

    def get(self, key: str) -> SummaryProfile:
        """Retourne un profil par sa clé.

        Args:
            key: Clé du profil recherché.

        Returns:
            Profil correspondant.

        Raises:
            KeyError: Si le profil n'existe pas.
        """
        return self._profiles[key]

    _CUSTOM_KEY: str = "custom"
    _CUSTOM_LABEL: str = "Personnalisé"
    _DEFAULT_CUSTOM_INSTRUCTION: str = (
        "Rédige un résumé personnalisé selon les instructions suivantes."
    )

    def available_profiles(self) -> list[SummaryProfile]:
        """Retourne la liste des profils triés par libellé."""
        return sorted(
            self._profiles.values(),
            key=lambda profile: profile.label,
        )

    @classmethod
    def build_custom_profile(
        cls,
        instruction: str = "",
    ) -> SummaryProfile:
        """Construit le profil personnalisé.

        Args:
            instruction: Instruction personnalisée. Si vide, une instruction
                par défaut est utilisée.

        Returns:
            Profil personnalisé.
        """
        return SummaryProfile(
            key=cls._CUSTOM_KEY,
            label=cls._CUSTOM_LABEL,
            instruction=instruction or cls._DEFAULT_CUSTOM_INSTRUCTION,
        )

    def available_profile_keys(self) -> set[str]:
        """Retourne l'ensemble des clés de profil disponibles.

        Returns:
            Clés des profils intégrés et du profil personnalisé.
        """
        return set(self._profiles.keys()) | {self._CUSTOM_KEY}

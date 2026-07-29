"""Tests du registre de profils de résumé."""

import unittest

from meetingai.services.summarization.summary_profile import (
    ProfileRegistry,
    SummaryProfile,
)


class TestProfileRegistry(unittest.TestCase):
    """Tests du registre des profils de résumé."""

    def setUp(self) -> None:
        """Crée un registre frais pour chaque test."""
        self.registry = ProfileRegistry()

    def test_default_profiles_are_available(self) -> None:
        """Les profils par défaut sont présents."""
        keys = {profile.key for profile in self.registry.available_profiles()}

        self.assertIn("concise", keys)
        self.assertIn("meeting_minutes", keys)
        self.assertIn("key_points", keys)
        self.assertIn("action_items", keys)
        self.assertIn("decisions", keys)

    def test_custom_profile_is_not_in_default_list(self) -> None:
        """Le profil personnalisé n'est pas dans les profils intégrés."""
        keys = {profile.key for profile in self.registry.available_profiles()}
        self.assertNotIn("custom", keys)

    def test_get_returns_profile(self) -> None:
        """get retourne le profil demandé."""
        profile = self.registry.get("concise")

        self.assertEqual(profile.key, "concise")
        self.assertEqual(profile.label, "Résumé concis")
        self.assertIsInstance(profile.instruction, str)

    def test_get_unknown_profile_raises_key_error(self) -> None:
        """get lève KeyError pour un profil inconnu."""
        with self.assertRaises(KeyError):
            self.registry.get("unknown")

    def test_available_profile_keys_includes_custom(self) -> None:
        """available_profile_keys inclut le profil personnalisé."""
        keys = self.registry.available_profile_keys()

        self.assertIn("concise", keys)
        self.assertIn("custom", keys)

    def test_build_custom_profile_uses_given_instruction(self) -> None:
        """build_custom_profile utilise l'instruction fournie."""
        profile = ProfileRegistry.build_custom_profile("Ma consigne.")

        self.assertEqual(profile.key, "custom")
        self.assertEqual(profile.label, "Personnalisé")
        self.assertEqual(profile.instruction, "Ma consigne.")

    def test_build_custom_profile_uses_default_instruction(self) -> None:
        """build_custom_profile utilise une instruction par défaut si vide."""
        profile = ProfileRegistry.build_custom_profile("")

        self.assertEqual(profile.key, "custom")
        self.assertTrue(profile.instruction)

    def test_register_adds_new_profile(self) -> None:
        """register permet d'ajouter un nouveau profil intégré."""
        profile = SummaryProfile(
            key="executive",
            label="Résumé exécutif",
            instruction="Résume pour un public exécutif.",
        )

        self.registry.register(profile)

        self.assertIn("executive", self.registry.available_profile_keys())
        self.assertEqual(self.registry.get("executive"), profile)


if __name__ == "__main__":
    unittest.main()

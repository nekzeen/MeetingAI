"""Tests du registre central des services."""

import unittest

from meetingai.core.service_registry import ServiceRegistry


class TestServiceRegistry(unittest.TestCase):
    """Tests de ServiceRegistry."""

    def setUp(self) -> None:
        """Réinitialise le registre avant chaque test."""
        ServiceRegistry._reset_instance()
        self.registry = ServiceRegistry()

    def tearDown(self) -> None:
        """Vide le registre après chaque test."""
        ServiceRegistry._reset_instance()

    def test_register_and_get(self) -> None:
        """Un service peut être enregistré puis récupéré."""
        service = object()
        self.registry.register("test_service", service)

        self.assertIs(self.registry.get("test_service"), service)

    def test_has_returns_true_for_registered_service(self) -> None:
        """``has`` retourne True pour un service enregistré."""
        self.registry.register("existing", object())

        self.assertTrue(self.registry.has("existing"))

    def test_has_returns_false_for_unknown_service(self) -> None:
        """``has`` retourne False pour un service inconnu."""
        self.assertFalse(self.registry.has("unknown"))

    def test_get_raises_keyerror_for_missing_service(self) -> None:
        """``get`` lève KeyError si le service n'existe pas."""
        with self.assertRaises(KeyError):
            self.registry.get("missing")

    def test_replace_existing_service(self) -> None:
        """Enregistrer à nouveau un nom remplace le service existant."""
        first = object()
        second = object()
        self.registry.register("service", first)
        self.registry.register("service", second)

        self.assertIs(self.registry.get("service"), second)

    def test_unregister_removes_service(self) -> None:
        """``unregister`` supprime un service enregistré."""
        self.registry.register("to_remove", object())
        self.registry.unregister("to_remove")

        self.assertFalse(self.registry.has("to_remove"))

    def test_unregister_raises_keyerror_for_unknown_service(self) -> None:
        """``unregister`` lève KeyError si le service n'existe pas."""
        with self.assertRaises(KeyError):
            self.registry.unregister("unknown")

    def test_clear_removes_all_services(self) -> None:
        """``clear`` vide le registre."""
        self.registry.register("first", object())
        self.registry.register("second", object())
        self.registry.clear()

        self.assertFalse(self.registry.has("first"))
        self.assertFalse(self.registry.has("second"))

    def test_singleton_returns_same_instance(self) -> None:
        """Le registre garantit une unique instance."""
        first = ServiceRegistry()
        second = ServiceRegistry()

        self.assertIs(first, second)

    def test_singleton_shares_services(self) -> None:
        """Les services sont partagés entre les appels au singleton."""
        service = object()
        ServiceRegistry().register("shared", service)

        self.assertIs(ServiceRegistry().get("shared"), service)


if __name__ == "__main__":
    unittest.main()

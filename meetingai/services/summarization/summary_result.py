"""Résultat d'un résumé IA."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SummaryResult:
    """Résultat d'une opération de résumé IA.

    Attributes:
        text: Texte résumé produit.
        provider: Identifiant du provider ayant généré le résumé.
    """

    text: str
    provider: str

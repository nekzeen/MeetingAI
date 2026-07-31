"""Capacités pouvant être fournies par un provider Runtime."""

from __future__ import annotations

from enum import Enum, auto


class RuntimeCapability(Enum):
    """Décrit une capacité fonctionnelle requise ou offerte par le Runtime.

    Chaque valeur correspond à un domaine métier de l'application. Un provider
    peut en déclarer plusieurs ; ``RuntimeManager`` peut ensuite vérifier qu'au
    moins un provider sain couvre chaque capacité requise.
    """

    SPEECH_TO_TEXT = "speech_to_text"
    GPU_ACCELERATION = "gpu_acceleration"
    SUMMARIZATION = "summarization"
    PDF_EXPORT = "pdf_export"
    DOCX_EXPORT = "docx_export"

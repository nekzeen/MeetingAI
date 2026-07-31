"""Couche Runtime de MeetingAI.

Ce package centralise la gestion des dépendances d'exécution (bibliothèques,
drivers, modèles) via une architecture extensible à base de providers.
"""

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_assistant import RuntimeAssistant
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_factory import create_runtime_manager
from meetingai.runtime.runtime_manager import RuntimeManager
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus

__all__ = [
    "RuntimeAction",
    "RuntimeActionType",
    "RuntimeAssistant",
    "RuntimeCapability",
    "RuntimeManager",
    "RuntimeProvider",
    "RuntimeReport",
    "RuntimeStatus",
    "create_runtime_manager",
]

"""Factory des instances Runtime par défaut de MeetingAI."""

from __future__ import annotations

from meetingai.runtime.providers import (
    CudaRuntimeProvider,
    FFmpegRuntimeProvider,
    OllamaRuntimeProvider,
    PythonRuntimeProvider,
    WhisperRuntimeProvider,
)
from meetingai.runtime.runtime_manager import RuntimeManager


def create_runtime_manager() -> RuntimeManager:
    """Crée et configure un ``RuntimeManager`` avec tous les providers standard.

    Returns:
        Gestionnaire Runtime prêt à l'emploi.
    """
    return RuntimeManager(
        providers=[
            PythonRuntimeProvider(),
            FFmpegRuntimeProvider(),
            WhisperRuntimeProvider(),
            OllamaRuntimeProvider(),
            CudaRuntimeProvider(),
        ],
    )

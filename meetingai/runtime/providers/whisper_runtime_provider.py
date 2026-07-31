"""Provider Runtime pour faster-whisper."""

from __future__ import annotations

import importlib.util
from importlib.metadata import PackageNotFoundError, version

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class WhisperRuntimeProvider(RuntimeProvider):
    """Vérifie la disponibilité de la bibliothèque faster-whisper.

    Ce provider ne modifie jamais le système.
    """

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "whisper"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la capacité de transcription."""
        return [RuntimeCapability.SPEECH_TO_TEXT]

    def status(self) -> RuntimeStatus:
        """Évalue rapidement la présence de faster-whisper."""
        if importlib.util.find_spec("faster_whisper") is None:
            return RuntimeStatus.MISSING
        return RuntimeStatus.HEALTHY

    def diagnose(self) -> RuntimeReport:
        """Diagnostique l'installation de faster-whisper et retourne sa version."""
        spec = importlib.util.find_spec("faster_whisper")
        if spec is None:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message="Le package faster-whisper n'est pas installé.",
                details={"package": "faster-whisper"},
            )

        try:
            whisper_version = version("faster-whisper")
        except PackageNotFoundError:
            whisper_version = "unknown"

        return RuntimeReport(
            provider_name=self.name,
            status=RuntimeStatus.HEALTHY,
            capabilities=self.capabilities,
            message=f"faster-whisper {whisper_version} est installé.",
            details={
                "package": "faster-whisper",
                "version": whisper_version,
            },
        )

    def can_install(self) -> bool:
        """L'installation automatique de faster-whisper n'est pas supportée."""
        return False

    def install(self) -> RuntimeReport:
        """Renvoie un rapport indiquant que l'installation n'est pas supportée."""
        return RuntimeReport(
            provider_name=self.name,
            status=self.status(),
            capabilities=self.capabilities,
            message="Installation automatique de faster-whisper non supportée.",
            details={},
        )

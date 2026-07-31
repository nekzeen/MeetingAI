"""Provider Runtime pour FFmpeg."""

from __future__ import annotations

import shutil
import subprocess

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class FFmpegRuntimeProvider(RuntimeProvider):
    """Vérifie la présence et l'accessibilité de FFmpeg.

    FFmpeg est utilisé indirectement par faster-whisper pour le décodage audio.
    Ce provider ne modifie jamais le système.
    """

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "ffmpeg"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la capacité de traitement média."""
        return [RuntimeCapability.MEDIA_PROCESSING]

    def status(self) -> RuntimeStatus:
        """Évalue rapidement la présence de FFmpeg."""
        if shutil.which("ffmpeg") is None:
            return RuntimeStatus.MISSING
        return RuntimeStatus.HEALTHY

    def diagnose(self) -> RuntimeReport:
        """Diagnostique l'installation FFmpeg et retourne sa version."""
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message="FFmpeg n'est pas trouvé dans le PATH.",
                details={"path": None},
            )

        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            version_line = result.stdout.splitlines()[0]
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"FFmpeg détecté : {version_line}.",
                details={
                    "path": ffmpeg_path,
                    "version": version_line,
                },
            )
        except (subprocess.SubprocessError, OSError) as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"FFmpeg trouvé mais impossible de lire la version : {exc}.",
                details={"path": ffmpeg_path, "error": str(exc)},
            )

    def can_install(self) -> bool:
        """L'installation automatique de FFmpeg n'est pas supportée."""
        return False

    def install(self) -> RuntimeReport:
        """Renvoie un rapport indiquant que l'installation n'est pas supportée."""
        return RuntimeReport(
            provider_name=self.name,
            status=self.status(),
            capabilities=self.capabilities,
            message="Installation automatique de FFmpeg non supportée.",
            details={},
        )

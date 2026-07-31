"""Provider Runtime pour l'environnement Python."""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class PythonRuntimeProvider(RuntimeProvider):
    """Diagnostique l'environnement Python et les packages installés.

    Ce provider ne modifie jamais le système. Il fournit des informations sur
    la version de Python, la plateforme et les packages clés utilisés par
    MeetingAI.
    """

    _MINIMAL_PYTHON_VERSION = (3, 12)
    _KEY_PACKAGES = [
        "faster-whisper",
        "PySide6",
        "reportlab",
        "python-docx",
    ]

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "python"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne les capacités couvertes (le runtime est transverse)."""
        return []

    def status(self) -> RuntimeStatus:
        """Évalue rapidement l'état de l'environnement Python."""
        if sys.version_info < self._MINIMAL_PYTHON_VERSION:
            return RuntimeStatus.DEGRADED
        return RuntimeStatus.HEALTHY

    def diagnose(self) -> RuntimeReport:
        """Diagnostique l'environnement Python et les packages clés."""
        python_version = ".".join(str(part) for part in sys.version_info[:3])
        status = self.status()

        packages: dict[str, str | None] = {}
        for package_name in self._KEY_PACKAGES:
            try:
                packages[package_name] = version(package_name)
            except PackageNotFoundError:
                packages[package_name] = None

        message = (
            f"Python {python_version} sur {platform.system()} "
            f"({platform.machine()})."
        )
        if status == RuntimeStatus.DEGRADED:
            message = (
                f"Version de Python {python_version} inférieure à "
                f"{'.'.join(str(part) for part in self._MINIMAL_PYTHON_VERSION)}."
            )

        return RuntimeReport(
            provider_name=self.name,
            status=status,
            message=message,
            details={
                "python_version": python_version,
                "platform": platform.system(),
                "architecture": platform.machine(),
                "packages": packages,
            },
        )

    def can_install(self) -> bool:
        """Le provider Python ne peut pas modifier l'interpréteur."""
        return False

    def install(self) -> RuntimeReport:
        """Renvoie un rapport indiquant que l'installation n'est pas supportée."""
        return RuntimeReport(
            provider_name=self.name,
            status=self.status(),
            message="Installation ou réparation non supportée par ce provider.",
            details={},
        )

"""Provider Runtime pour CUDA / accélération GPU."""

from __future__ import annotations

import importlib.util
import subprocess

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class CudaRuntimeProvider(RuntimeProvider):
    """Vérifie la disponibilité de l'accélération GPU via CUDA.

    Ce provider ne modifie jamais le système. Il tente d'abord d'utiliser
    ``torch.cuda`` si torch est installé, puis tombe sur ``nvidia-smi`` en
    cas d'indisponibilité.
    """

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "cuda"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la capacité d'accélération GPU."""
        return [RuntimeCapability.GPU_ACCELERATION]

    def status(self) -> RuntimeStatus:
        """Évalue rapidement la disponibilité de CUDA."""
        if self._torch_cuda_available():
            return RuntimeStatus.HEALTHY
        if self._nvidia_smi_available():
            return RuntimeStatus.HEALTHY
        if self._torch_present():
            return RuntimeStatus.DEGRADED
        return RuntimeStatus.UNKNOWN

    def diagnose(self) -> RuntimeReport:
        """Diagnostique CUDA via torch ou nvidia-smi."""
        if self._torch_cuda_available():
            return self._torch_report(RuntimeStatus.HEALTHY)
        if self._nvidia_smi_available():
            return self._nvidia_smi_report(RuntimeStatus.HEALTHY)
        if self._torch_present():
            return self._torch_report(RuntimeStatus.DEGRADED)
        return RuntimeReport(
            provider_name=self.name,
            status=RuntimeStatus.UNKNOWN,
            capabilities=self.capabilities,
            message="Impossible de déterminer l'état CUDA (ni torch ni nvidia-smi).",
            details={},
        )

    def _torch_present(self) -> bool:
        """Indique si le package torch est installé."""
        return importlib.util.find_spec("torch") is not None

    def _torch_cuda_available(self) -> bool:
        """Vérifie torch.cuda.is_available() si torch est installé."""
        if not self._torch_present():
            return False
        try:
            import torch

            return bool(torch.cuda.is_available())
        except Exception:  # pragma: no cover - défense large
            return False

    def _torch_report(self, status: RuntimeStatus) -> RuntimeReport:
        """Construit un rapport à partir des informations torch."""
        details: dict[str, object] = {}
        message = "torch est installé mais CUDA n'est pas disponible."
        try:
            import torch

            details["torch_version"] = torch.__version__
            if torch.cuda.is_available():
                details["cuda_version"] = torch.version.cuda
                details["device_count"] = torch.cuda.device_count()
                details["device_name"] = torch.cuda.get_device_name(0)
                message = f"CUDA disponible via torch : {details['device_name']}."
            else:
                details["cuda_available"] = False
        except Exception as exc:  # pragma: no cover
            message = f"torch présent mais informations CUDA indisponibles : {exc}."
            details["error"] = str(exc)

        return RuntimeReport(
            provider_name=self.name,
            status=status,
            capabilities=self.capabilities,
            message=message,
            details=details,
        )

    def _nvidia_smi_available(self) -> bool:
        """Vérifie si nvidia-smi est accessible."""
        try:
            subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    def _nvidia_smi_report(self, status: RuntimeStatus) -> RuntimeReport:
        """Construit un rapport à partir de nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            line = result.stdout.strip().split(",")
            device_name = line[0].strip() if line else "unknown"
            driver_version = line[1].strip() if len(line) > 1 else "unknown"
            return RuntimeReport(
                provider_name=self.name,
                status=status,
                capabilities=self.capabilities,
                message=f"GPU détecté via nvidia-smi : {device_name}.",
                details={
                    "device_name": device_name,
                    "driver_version": driver_version,
                },
            )
        except (subprocess.SubprocessError, OSError) as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.DEGRADED,
                capabilities=self.capabilities,
                message=f"nvidia-smi présent mais lecture impossible : {exc}.",
                details={"error": str(exc)},
            )

    def can_install(self) -> bool:
        """L'installation automatique de CUDA n'est pas supportée."""
        return False

    def install(self) -> RuntimeReport:
        """Renvoie un rapport indiquant que l'installation n'est pas supportée."""
        return RuntimeReport(
            provider_name=self.name,
            status=self.status(),
            capabilities=self.capabilities,
            message="Installation automatique de CUDA non supportée.",
            details={},
        )

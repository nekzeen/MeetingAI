"""Tests des providers Runtime concrets."""

from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import MagicMock, patch

from meetingai.runtime.providers import (
    CudaRuntimeProvider,
    FFmpegRuntimeProvider,
    OllamaRuntimeProvider,
    PythonRuntimeProvider,
    WhisperRuntimeProvider,
)
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_status import RuntimeStatus


class TestPythonRuntimeProvider(unittest.TestCase):
    """Tests du provider Python."""

    def test_name_and_capabilities(self) -> None:
        """Le provider expose le bon nom et aucune capacité métier."""
        provider = PythonRuntimeProvider()
        self.assertEqual(provider.name, "python")
        self.assertEqual(provider.capabilities, [])

    def test_diagnose_is_healthy(self) -> None:
        """Le diagnostic retourne un rapport HEALTHY pour Python actuel."""
        provider = PythonRuntimeProvider()
        report = provider.diagnose()

        self.assertEqual(report.provider_name, "python")
        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertIn("python_version", report.details)
        self.assertIn("packages", report.details)

    def test_can_install_is_false(self) -> None:
        """Le provider Python ne peut pas s'installer lui-même."""
        provider = PythonRuntimeProvider()
        self.assertFalse(provider.can_install())
        install_report = provider.install()
        self.assertEqual(install_report.provider_name, "python")


class TestWhisperRuntimeProvider(unittest.TestCase):
    """Tests du provider faster-whisper."""

    def test_name_and_capabilities(self) -> None:
        """Le provider couvre la transcription."""
        provider = WhisperRuntimeProvider()
        self.assertEqual(provider.name, "whisper")
        self.assertEqual(
            provider.capabilities,
            [RuntimeCapability.SPEECH_TO_TEXT],
        )

    @patch("meetingai.runtime.providers.whisper_runtime_provider.importlib.util.find_spec")
    def test_diagnose_missing_package(self, mock_find_spec: MagicMock) -> None:
        """Le diagnostic signale MISSING si faster-whisper n'est pas installé."""
        mock_find_spec.return_value = None
        provider = WhisperRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.MISSING)
        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.MISSING)
        self.assertIn("faster-whisper", report.message.lower())

    @patch(
        "meetingai.runtime.providers.whisper_runtime_provider.importlib.util.find_spec"
    )
    @patch("meetingai.runtime.providers.whisper_runtime_provider.version")
    def test_diagnose_installed_package(
        self,
        mock_version: MagicMock,
        mock_find_spec: MagicMock,
    ) -> None:
        """Le diagnostic retourne HEALTHY avec la version du package."""
        mock_find_spec.return_value = MagicMock()
        mock_version.return_value = "0.10.0"
        provider = WhisperRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.HEALTHY)
        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("version"), "0.10.0")

    def test_install_not_supported(self) -> None:
        """L'installation automatique n'est pas supportée."""
        provider = WhisperRuntimeProvider()
        self.assertFalse(provider.can_install())


class TestFFmpegRuntimeProvider(unittest.TestCase):
    """Tests du provider FFmpeg."""

    def test_name_and_capabilities(self) -> None:
        """Le provider couvre le traitement média."""
        provider = FFmpegRuntimeProvider()
        self.assertEqual(provider.name, "ffmpeg")
        self.assertEqual(
            provider.capabilities,
            [RuntimeCapability.MEDIA_PROCESSING],
        )

    @patch("meetingai.runtime.providers.ffmpeg_runtime_provider.shutil.which")
    def test_diagnose_missing_binary(self, mock_which: MagicMock) -> None:
        """Le diagnostic signale MISSING si FFmpeg n'est pas dans le PATH."""
        mock_which.return_value = None
        provider = FFmpegRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.MISSING)
        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.MISSING)
        self.assertIn("path", report.details)

    @patch("meetingai.runtime.providers.ffmpeg_runtime_provider.shutil.which")
    @patch("meetingai.runtime.providers.ffmpeg_runtime_provider.subprocess.run")
    def test_diagnose_installed_binary(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Le diagnostic retourne HEALTHY avec la version de FFmpeg."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        result = MagicMock()
        result.stdout = "ffmpeg version 6.0\n"
        result.returncode = 0
        mock_run.return_value = result
        provider = FFmpegRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.HEALTHY)
        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("path"), "/usr/bin/ffmpeg")


class TestOllamaRuntimeProvider(unittest.TestCase):
    """Tests du provider Ollama."""

    def test_name_and_capabilities(self) -> None:
        """Le provider couvre la summarization."""
        provider = OllamaRuntimeProvider()
        self.assertEqual(provider.name, "ollama")
        self.assertEqual(
            provider.capabilities,
            [RuntimeCapability.SUMMARIZATION],
        )

    @patch("meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec")
    @patch("meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen")
    def test_diagnose_server_available(
        self,
        mock_urlopen: MagicMock,
        mock_find_spec: MagicMock,
    ) -> None:
        """Le diagnostic retourne HEALTHY si le serveur répond."""
        mock_find_spec.return_value = MagicMock()
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"models": [{"name": "llama3"}]}
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = response
        provider = OllamaRuntimeProvider()

        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertIn("llama3", report.details.get("models", []))

    @patch("meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec")
    @patch("meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen")
    def test_diagnose_server_unreachable(
        self,
        mock_urlopen: MagicMock,
        mock_find_spec: MagicMock,
    ) -> None:
        """Le diagnostic retourne MISSING si le serveur n'est pas accessible."""
        import urllib.error

        mock_find_spec.return_value = None
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        provider = OllamaRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.MISSING)
        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.MISSING)
        self.assertIn("host", report.details)


class TestCudaRuntimeProvider(unittest.TestCase):
    """Tests du provider CUDA."""

    def test_name_and_capabilities(self) -> None:
        """Le provider couvre l'accélération GPU."""
        provider = CudaRuntimeProvider()
        self.assertEqual(provider.name, "cuda")
        self.assertEqual(
            provider.capabilities,
            [RuntimeCapability.GPU_ACCELERATION],
        )

    @patch(
        "meetingai.runtime.providers.cuda_runtime_provider.importlib.util.find_spec"
    )
    @patch.dict("sys.modules", {})
    def test_diagnose_torch_cuda_available(
        self,
        mock_find_spec: MagicMock,
    ) -> None:
        """Le diagnostic retourne HEALTHY si torch.cuda.is_available()."""
        mock_find_spec.return_value = MagicMock()
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.3.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "12.1"
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce"
        sys.modules["torch"] = mock_torch
        provider = CudaRuntimeProvider()

        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("device_name"), "NVIDIA GeForce")

    @patch(
        "meetingai.runtime.providers.cuda_runtime_provider.CudaRuntimeProvider._nvidia_smi_available"
    )
    @patch(
        "meetingai.runtime.providers.cuda_runtime_provider.importlib.util.find_spec"
    )
    def test_diagnose_no_torch_no_nvidia_smi(
        self,
        mock_find_spec: MagicMock,
        mock_nvidia_smi: MagicMock,
    ) -> None:
        """Le diagnostic retourne UNKNOWN si torch et nvidia-smi sont absents."""
        mock_find_spec.return_value = None
        mock_nvidia_smi.return_value = False
        provider = CudaRuntimeProvider()

        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.UNKNOWN)

    def test_install_not_supported(self) -> None:
        """L'installation automatique n'est pas supportée."""
        provider = CudaRuntimeProvider()
        self.assertFalse(provider.can_install())


if __name__ == "__main__":
    unittest.main()

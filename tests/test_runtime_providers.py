"""Tests des providers Runtime concrets."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
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
    """Tests du provider faster-whisper et de la gestion des modèles."""

    def _create_valid_model(self, root: str, name: str = "small") -> Path:
        """Crée un répertoire de modèle valide avec les fichiers requis."""
        model_dir = Path(root) / name
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "config.json").touch()
        (model_dir / "model.bin").touch()
        return model_dir

    def test_name_and_capabilities(self) -> None:
        """Le provider couvre la transcription."""
        provider = WhisperRuntimeProvider()
        self.assertEqual(provider.name, "whisper")
        self.assertEqual(
            provider.capabilities,
            [RuntimeCapability.SPEECH_TO_TEXT],
        )

    @patch(
        "meetingai.runtime.providers.whisper_runtime_provider.importlib.util.find_spec"
    )
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
    def test_diagnose_installed_package_and_model(
        self,
        mock_version: MagicMock,
        mock_find_spec: MagicMock,
    ) -> None:
        """Le diagnostic retourne HEALTHY si le package et le modèle sont présents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_valid_model(tmp_dir)
            mock_find_spec.return_value = MagicMock()
            mock_version.return_value = "0.10.0"
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            self.assertEqual(provider.status(), RuntimeStatus.HEALTHY)
            report = provider.diagnose()

            self.assertEqual(report.status, RuntimeStatus.HEALTHY)
            self.assertEqual(report.details.get("version"), "0.10.0")
            self.assertIn("small", report.details.get("installed_models", []))

    @patch(
        "meetingai.runtime.providers.whisper_runtime_provider.importlib.util.find_spec"
    )
    @patch("meetingai.runtime.providers.whisper_runtime_provider.version")
    def test_diagnose_installed_package_missing_model(
        self,
        mock_version: MagicMock,
        mock_find_spec: MagicMock,
    ) -> None:
        """Le diagnostic retourne MISSING si le modèle n'est pas présent."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_find_spec.return_value = MagicMock()
            mock_version.return_value = "0.10.0"
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            self.assertEqual(provider.status(), RuntimeStatus.MISSING)
            report = provider.diagnose()

            self.assertEqual(report.status, RuntimeStatus.MISSING)
            self.assertIn("small", report.message)

    def test_is_model_present_requires_required_files(self) -> None:
        """is_model_present retourne False si les fichiers requis sont absents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "small").mkdir()
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            self.assertFalse(provider.is_model_present())

    def test_is_model_present_true_when_valid(self) -> None:
        """is_model_present retourne True si le modèle est complet."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_valid_model(tmp_dir)
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            self.assertTrue(provider.is_model_present())

    def test_list_installed_models(self) -> None:
        """list_installed_models retourne les modèles valides du répertoire."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_valid_model(tmp_dir, "small")
            self._create_valid_model(tmp_dir, "tiny")
            (Path(tmp_dir) / "empty").mkdir()
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            models = provider.list_installed_models()

            self.assertEqual(models, ["small", "tiny"])

    @patch.object(WhisperRuntimeProvider, "_has_package", return_value=True)
    @patch.object(
        WhisperRuntimeProvider,
        "_faster_whisper_module",
        return_value=MagicMock(download_model=lambda _s, output_dir: output_dir),
    )
    def test_install_model_success(
        self,
        mock_module: MagicMock,
        mock_package: MagicMock,
    ) -> None:
        """install_model retourne HEALTHY en cas de succès."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)
            report = provider.install_model("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.HEALTHY)
            self.assertIn("model_path", report.details)

    @patch.object(WhisperRuntimeProvider, "_has_package", return_value=False)
    def test_install_model_fails_when_package_missing(
        self,
        mock_package: MagicMock,
    ) -> None:
        """install_model retourne MISSING si faster-whisper n'est pas installé."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)
            report = provider.install_model("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.MISSING)

    @patch.object(WhisperRuntimeProvider, "_has_package", return_value=True)
    @patch.object(
        WhisperRuntimeProvider,
        "_faster_whisper_module",
        return_value=MagicMock(
            download_model=MagicMock(side_effect=RuntimeError("network down"))
        ),
    )
    def test_install_model_reports_error(
        self,
        mock_module: MagicMock,
        mock_package: MagicMock,
    ) -> None:
        """install_model retourne ERROR en cas d'échec de téléchargement."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)
            report = provider.install_model("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.ERROR)
            self.assertIn("network down", report.message)

    @patch.object(WhisperRuntimeProvider, "_has_package", return_value=True)
    def test_install_delegates_to_install_model(
        self,
        mock_package: MagicMock,
    ) -> None:
        """install() appelle install_model avec le modèle configuré."""
        provider = WhisperRuntimeProvider()
        provider.install_model = MagicMock(return_value=MagicMock(status=RuntimeStatus.HEALTHY))  # type: ignore[assignment]

        provider.install()

        provider.install_model.assert_called_once_with("small", Path("models"))

    def test_remove_model_success(self) -> None:
        """remove_model supprime le répertoire du modèle."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_valid_model(tmp_dir)
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            report = provider.remove_model("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.HEALTHY)
            self.assertFalse(provider.is_model_present("small", tmp_dir))

    def test_remove_model_missing(self) -> None:
        """remove_model retourne MISSING si le modèle n'existe pas."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)
            report = provider.remove_model("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.MISSING)

    def test_verify_model_integrity_healthy(self) -> None:
        """verify_model_integrity retourne HEALTHY pour un modèle complet."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_valid_model(tmp_dir)
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            report = provider.verify_model_integrity("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.HEALTHY)

    def test_verify_model_integrity_error_when_files_missing(self) -> None:
        """verify_model_integrity retourne ERROR si des fichiers sont manquants."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            (Path(tmp_dir) / "small").mkdir()
            (Path(tmp_dir) / "small" / "config.json").touch()
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)

            report = provider.verify_model_integrity("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.ERROR)
            self.assertIn("model.bin", report.details.get("missing_files", []))

    def test_can_install_when_package_present(self) -> None:
        """can_install retourne True si faster-whisper est installé."""
        with patch.object(WhisperRuntimeProvider, "_has_package", return_value=True):
            provider = WhisperRuntimeProvider()
            self.assertTrue(provider.can_install())

    def test_cannot_install_when_package_missing(self) -> None:
        """can_install retourne False si faster-whisper est manquant."""
        with patch.object(WhisperRuntimeProvider, "_has_package", return_value=False):
            provider = WhisperRuntimeProvider()
            self.assertFalse(provider.can_install())


    def test_install_model_downloads_to_model_subdirectory(self) -> None:
        """install_model télécharge dans models_directory / model_size."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider = WhisperRuntimeProvider(models_directory=tmp_dir)
            model_dir = Path(tmp_dir) / "small"
            fake_module = MagicMock()
            fake_module.download_model = MagicMock(return_value=str(model_dir))

            with patch.object(
                provider,
                "_faster_whisper_module",
                return_value=fake_module,
            ):
                report = provider.install_model("small", tmp_dir)

            self.assertEqual(report.status, RuntimeStatus.HEALTHY)
            self.assertEqual(Path(report.details["model_path"]), model_dir)
            fake_module.download_model.assert_called_once_with(
                "small", output_dir=str(model_dir)
            )


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
    """Tests du provider Ollama et de la gestion des modèles."""

    def _urlopen_response(self, payload: dict) -> MagicMock:
        """Construit un objet de réponse simulé pour urllib.request.urlopen."""
        response = MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        return response

    def test_name_and_capabilities(self) -> None:
        """Le provider couvre la summarization."""
        provider = OllamaRuntimeProvider()
        self.assertEqual(provider.name, "ollama")
        self.assertEqual(
            provider.capabilities,
            [RuntimeCapability.SUMMARIZATION],
        )

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_is_ollama_present_detects_package(
        self,
        mock_urlopen: MagicMock,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """is_ollama_present détecte le package Python."""
        mock_find_spec.return_value = MagicMock()
        mock_which.return_value = None
        provider = OllamaRuntimeProvider()

        self.assertTrue(provider.is_ollama_present())

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    def test_is_ollama_present_detects_binary(
        self,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """is_ollama_present détecte le binaire système."""
        mock_find_spec.return_value = None
        mock_which.return_value = "/usr/bin/ollama"
        provider = OllamaRuntimeProvider()

        self.assertTrue(provider.is_ollama_present())

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_get_version_returns_version(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """get_version retourne la version du serveur."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"version": "0.5.0"}
        )
        provider = OllamaRuntimeProvider()

        report = provider.get_version()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("version"), "0.5.0")

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_list_installed_models_returns_sorted_names(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """list_installed_models retourne les modèles installés."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {
                "models": [
                    {"name": "mistral"},
                    {"name": "llama3.2"},
                ]
            }
        )
        provider = OllamaRuntimeProvider()

        report = provider.list_installed_models()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("models"), ["llama3.2", "mistral"])

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_is_model_available_true_when_installed(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """is_model_available retourne HEALTHY si le modèle est installé."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"models": [{"name": "llama3.2"}]}
        )
        provider = OllamaRuntimeProvider()

        report = provider.is_model_available("llama3.2")

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("model"), "llama3.2")

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_is_model_available_false_when_missing(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """is_model_available retourne MISSING si le modèle n'est pas installé."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"models": [{"name": "llama3"}]}
        )
        provider = OllamaRuntimeProvider()

        report = provider.is_model_available("llama3.2")

        self.assertEqual(report.status, RuntimeStatus.MISSING)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_install_model_pulls_model(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """install_model appelle l'API pull."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"status": "success"}
        )
        provider = OllamaRuntimeProvider()

        report = provider.install_model("llama3.2")

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        called_request = mock_urlopen.call_args[0][0]
        self.assertEqual(called_request.get_full_url().split("/")[-1], "pull")

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_remove_model_deletes_model(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """remove_model appelle l'API delete."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"success": True}
        )
        provider = OllamaRuntimeProvider()

        report = provider.remove_model("llama3.2")

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        called_request = mock_urlopen.call_args[0][0]
        self.assertEqual(called_request.get_method(), "DELETE")

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_generate_returns_response(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """generate retourne la réponse Ollama."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"response": "Résumé généré."}
        )
        provider = OllamaRuntimeProvider()

        report = provider.generate("Texte à résumer.", "llama3.2")

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertEqual(report.details.get("response"), "Résumé généré.")

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_status_healthy(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """status retourne HEALTHY si le modèle configuré est installé."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"models": [{"name": "llama3.2"}]}
        )
        provider = OllamaRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.HEALTHY)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_status_degraded_when_model_missing(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """status retourne DEGRADED si le modèle par défaut est manquant."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"models": [{"name": "llama3"}]}
        )
        provider = OllamaRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.DEGRADED)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_status_missing_when_server_unreachable(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """status retourne MISSING si le serveur ne répond pas."""
        import urllib.error

        mock_which.return_value = None
        mock_find_spec = None
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        provider = OllamaRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.MISSING)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_can_install_when_server_reachable(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """can_install retourne True si le serveur est joignable."""
        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"models": []}
        )
        provider = OllamaRuntimeProvider()

        self.assertTrue(provider.can_install())

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_cannot_install_when_server_unreachable(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """can_install retourne False si le serveur est inaccessible."""
        import urllib.error

        mock_which.return_value = "/usr/bin/ollama"
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        provider = OllamaRuntimeProvider()

        self.assertFalse(provider.can_install())

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_diagnose_server_available(
        self,
        mock_urlopen: MagicMock,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Le diagnostic retourne HEALTHY si le serveur répond."""
        mock_find_spec.return_value = MagicMock()
        mock_which.return_value = None
        mock_urlopen.return_value.__enter__.return_value = self._urlopen_response(
            {"models": [{"name": "llama3.2"}]}
        )
        provider = OllamaRuntimeProvider()

        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertIn("llama3.2", report.details.get("installed_models", []))

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.urllib.request.urlopen"
    )
    def test_diagnose_server_unreachable(
        self,
        mock_urlopen: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Le diagnostic retourne MISSING si le serveur n'est pas accessible."""
        import urllib.error

        mock_which.return_value = None
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        provider = OllamaRuntimeProvider()

        self.assertEqual(provider.status(), RuntimeStatus.MISSING)
        report = provider.diagnose()

        self.assertEqual(report.status, RuntimeStatus.MISSING)
        self.assertIn("host", report.details)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.subprocess.Popen"
    )
    def test_start_server_not_installed(
        self,
        mock_popen: MagicMock,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """start_server retourne MISSING si Ollama n'est pas installé."""
        mock_find_spec.return_value = None
        mock_which.return_value = None
        provider = OllamaRuntimeProvider()

        report = provider.start_server()

        self.assertEqual(report.status, RuntimeStatus.MISSING)
        mock_popen.assert_not_called()

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.time.sleep"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.subprocess.Popen"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    def test_start_server_success(
        self,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
        mock_popen: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """start_server démarre le binaire et retourne HEALTHY quand le serveur répond."""
        mock_find_spec.return_value = None
        mock_which.return_value = "/usr/bin/ollama"
        provider = OllamaRuntimeProvider()

        with patch.object(
            provider, "is_server_reachable", side_effect=[False, True]
        ):
            report = provider.start_server()

        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertIn("démarré", report.message)
        mock_popen.assert_called_once()
        mock_sleep.assert_called_once_with(0.5)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.time.sleep"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.subprocess.Popen"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    def test_start_server_timeout(
        self,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
        mock_popen: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """start_server retourne ERROR si le serveur ne répond pas dans le délai."""
        mock_find_spec.return_value = None
        mock_which.return_value = "/usr/bin/ollama"
        provider = OllamaRuntimeProvider()

        with patch.object(
            provider, "is_server_reachable", side_effect=[False] * 31
        ):
            report = provider.start_server()

        self.assertEqual(report.status, RuntimeStatus.ERROR)
        self.assertIn("délai", report.message)
        self.assertEqual(mock_popen.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 30)

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    def test_can_start_server(
        self,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """can_start_server retourne True si Ollama est installé mais le serveur est arrêté."""
        mock_find_spec.return_value = None
        mock_which.return_value = "/usr/bin/ollama"
        provider = OllamaRuntimeProvider()

        with patch.object(provider, "is_server_reachable", return_value=False):
            self.assertTrue(provider.can_start_server())

    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.shutil.which"
    )
    @patch(
        "meetingai.runtime.providers.ollama_runtime_provider.importlib.util.find_spec"
    )
    def test_cannot_start_server_when_ollama_missing(
        self,
        mock_find_spec: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """can_start_server retourne False si Ollama n'est pas installé."""
        mock_find_spec.return_value = None
        mock_which.return_value = None
        provider = OllamaRuntimeProvider()

        self.assertFalse(provider.can_start_server())

    def test_set_model_changes_active_model(self) -> None:
        """set_model met à jour le modèle configuré."""
        provider = OllamaRuntimeProvider()

        report = provider.set_model("mistral")

        self.assertEqual(provider.model, "mistral")
        self.assertEqual(report.status, RuntimeStatus.HEALTHY)
        self.assertIn("mistral", report.message)


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

"""Provider Runtime pour faster-whisper et ses modèles."""

from __future__ import annotations

import importlib.util
import logging
import shutil
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import ModuleType
from typing import Any

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus

_LOGGER = logging.getLogger(__name__)


class WhisperRuntimeProvider(RuntimeProvider):
    """Gère le runtime faster-whisper : bibliothèque et modèles locaux.

    Ce provider est le gestionnaire unique des modèles Whisper. Il offre des
    opérations de diagnostic, d'installation, de suppression et de vérification
    d'intégrité. Toutes les opérations retournent un ``RuntimeReport``.
    """

    _DEFAULT_MODEL_SIZE: str = "small"
    _DEFAULT_MODELS_DIRECTORY: Path = Path("models")
    _REQUIRED_FILES: tuple[str, ...] = (
        "config.json",
        "model.bin",
    )

    def __init__(
        self,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> None:
        """Initialise le provider avec le modèle et le répertoire par défaut."""
        self._model_size = model_size or self._DEFAULT_MODEL_SIZE
        self._models_directory = (
            Path(models_directory)
            if models_directory is not None
            else self._DEFAULT_MODELS_DIRECTORY
        )

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "whisper"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la capacité de transcription."""
        return [RuntimeCapability.SPEECH_TO_TEXT]

    @property
    def model_size(self) -> str:
        """Retourne la taille du modèle configuré."""
        return self._model_size

    @property
    def models_directory(self) -> Path:
        """Retourne le répertoire racine des modèles configuré."""
        return self._models_directory

    def _has_package(self) -> bool:
        """Indique si le package faster-whisper est installé."""
        return importlib.util.find_spec("faster_whisper") is not None

    def _package_version(self) -> str:
        """Retourne la version du package faster-whisper."""
        try:
            return version("faster-whisper")
        except PackageNotFoundError:
            return "unknown"

    def _faster_whisper_module(self) -> ModuleType | None:
        """Importe faster-whisper sans échouer à l'import du module."""
        if not self._has_package():
            return None
        try:
            import faster_whisper  # type: ignore

            return faster_whisper
        except Exception as exc:  # pragma: no cover - défense large
            _LOGGER.warning("Import faster-whisper échoué : %s", exc)
            return None

    def model_path(
        self,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> Path:
        """Retourne le chemin attendu pour un modèle donné."""
        size = model_size or self._model_size
        directory = (
            Path(models_directory)
            if models_directory is not None
            else self._models_directory
        )
        return directory / size

    def is_model_present(
        self,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> bool:
        """Indique si le répertoire du modèle existe et contient les fichiers requis."""
        path = self.model_path(model_size, models_directory)
        if not path.is_dir():
            return False
        return all((path / required).exists() for required in self._REQUIRED_FILES)

    def list_installed_models(
        self,
        models_directory: str | Path | None = None,
    ) -> list[str]:
        """Liste les modèles valides présents dans le répertoire."""
        directory = (
            Path(models_directory)
            if models_directory is not None
            else self._models_directory
        )
        if not directory.exists():
            return []

        return sorted(
            item.name
            for item in directory.iterdir()
            if item.is_dir()
            and all((item / required).exists() for required in self._REQUIRED_FILES)
        )

    def status(self) -> RuntimeStatus:
        """Évalue rapidement l'état du package et du modèle configuré."""
        if not self._has_package():
            return RuntimeStatus.MISSING
        if self.is_model_present(self._model_size, self._models_directory):
            return RuntimeStatus.HEALTHY
        return RuntimeStatus.MISSING

    def diagnose(self) -> RuntimeReport:
        """Diagnostique le package faster-whisper et le modèle configuré."""
        package_version = self._package_version()
        installed_models = self.list_installed_models()
        model_present = self.is_model_present()

        if not self._has_package():
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message="Le package faster-whisper n'est pas installé.",
                details={
                    "package": "faster-whisper",
                    "installed_models": installed_models,
                    "model_path": str(self.model_path()),
                },
            )

        if not model_present:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=(
                    f"faster-whisper {package_version} est installé mais le "
                    f"modèle '{self._model_size}' n'est pas présent dans "
                    f"{self._models_directory}."
                ),
                details={
                    "package": "faster-whisper",
                    "version": package_version,
                    "installed_models": installed_models,
                    "model_size": self._model_size,
                    "model_path": str(self.model_path()),
                },
            )

        return RuntimeReport(
            provider_name=self.name,
            status=RuntimeStatus.HEALTHY,
            capabilities=self.capabilities,
            message=(
                f"faster-whisper {package_version} et le modèle "
                f"'{self._model_size}' sont présents."
            ),
            details={
                "package": "faster-whisper",
                "version": package_version,
                "installed_models": installed_models,
                "model_size": self._model_size,
                "model_path": str(self.model_path()),
            },
        )

    def can_install(self) -> bool:
        """L'installation d'un modèle est possible si faster-whisper est présent."""
        return self._has_package()

    def install(self) -> RuntimeReport:
        """Installe le modèle configuré via faster-whisper."""
        return self.install_model(self._model_size, self._models_directory)

    def suggested_actions(self, report: RuntimeReport) -> list[RuntimeAction]:
        """Propose des actions d'installation ou de téléchargement de modèle."""
        if report.status == RuntimeStatus.HEALTHY:
            return []

        if not self._has_package():
            return [
                RuntimeAction(
                    action_type=RuntimeActionType.INSTALL_PACKAGE,
                    provider_name=self.name,
                    message="Installer faster-whisper.",
                    description="Le package faster-whisper n'est pas installé.",
                    available=False,
                    requires_user=True,
                    parameters={"package": "faster-whisper"},
                )
            ]

        if not self.is_model_present(self._model_size, self._models_directory):
            return [
                RuntimeAction(
                    action_type=RuntimeActionType.DOWNLOAD_MODEL,
                    provider_name=self.name,
                    message=f"Télécharger le modèle Whisper '{self._model_size}'.",
                    description=f"Le modèle est absent de {self._models_directory}.",
                    available=True,
                    requires_user=True,
                    parameters={
                        "model_size": self._model_size,
                        "model_path": str(self.model_path()),
                    },
                )
            ]

        return super().suggested_actions(report)

    def install_model(
        self,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> RuntimeReport:
        """Télécharge un modèle faster-whisper.

        Returns:
            Rapport décrivant le résultat du téléchargement.
        """
        size = model_size or self._model_size
        directory = (
            Path(models_directory)
            if models_directory is not None
            else self._models_directory
        )

        if not self._has_package():
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message="Impossible d'installer un modèle : faster-whisper n'est pas installé.",
                details={"model_size": size, "model_path": str(directory / size)},
            )

        faster_whisper = self._faster_whisper_module()
        if faster_whisper is None:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message="Import de faster-whisper échoué.",
                details={"model_size": size, "model_path": str(directory / size)},
            )

        try:
            downloaded_path = Path(
                faster_whisper.download_model(size, output_dir=directory)
            )
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Modèle '{size}' téléchargé avec succès.",
                details={
                    "model_size": size,
                    "model_path": str(downloaded_path),
                },
            )
        except Exception as exc:
            _LOGGER.warning("Échec du téléchargement du modèle '%s' : %s", size, exc)
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec du téléchargement du modèle '{size}' : {exc}.",
                details={
                    "model_size": size,
                    "model_path": str(directory / size),
                    "error": str(exc),
                },
            )

    def remove_model(
        self,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> RuntimeReport:
        """Supprime un modèle local.

        Returns:
            Rapport décrivant le résultat de la suppression.
        """
        path = self.model_path(model_size, models_directory)

        if not path.exists():
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=f"Le modèle '{path.name}' n'existe pas.",
                details={"model_path": str(path)},
            )

        try:
            shutil.rmtree(path)
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Modèle '{path.name}' supprimé avec succès.",
                details={"model_path": str(path)},
            )
        except OSError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec de la suppression du modèle '{path.name}' : {exc}.",
                details={"model_path": str(path), "error": str(exc)},
            )

    def verify_model_integrity(
        self,
        model_size: str | None = None,
        models_directory: str | Path | None = None,
    ) -> RuntimeReport:
        """Vérifie que les fichiers requis du modèle sont présents.

        Returns:
            Rapport de vérification d'intégrité.
        """
        path = self.model_path(model_size, models_directory)

        if not path.is_dir():
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=f"Le répertoire du modèle '{path.name}' est introuvable.",
                details={"model_path": str(path)},
            )

        missing = [
            required for required in self._REQUIRED_FILES if not (path / required).exists()
        ]
        if missing:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=(
                    f"Fichiers manquants dans le modèle '{path.name}' : "
                    f"{', '.join(missing)}."
                ),
                details={
                    "model_path": str(path),
                    "missing_files": missing,
                    "required_files": list(self._REQUIRED_FILES),
                },
            )

        return RuntimeReport(
            provider_name=self.name,
            status=RuntimeStatus.HEALTHY,
            capabilities=self.capabilities,
            message=f"Le modèle '{path.name}' est complet.",
            details={
                "model_path": str(path),
                "required_files": list(self._REQUIRED_FILES),
            },
        )

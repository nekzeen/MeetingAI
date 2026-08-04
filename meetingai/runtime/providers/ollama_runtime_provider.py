"""Provider Runtime pour Ollama et ses modèles."""

from __future__ import annotations

import importlib.util
import json
import logging
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus

_LOGGER = logging.getLogger(__name__)


class OllamaRuntimeProvider(RuntimeProvider):
    """Gère le runtime Ollama : binaire, serveur et modèles locaux.

    Ce provider est le gestionnaire unique d'Ollama. Toutes les opérations de
    détection, de diagnostic, d'installation et de suppression retournent un
    ``RuntimeReport``.
    """

    _DEFAULT_HOST: str = "http://localhost:11434"
    _DEFAULT_MODEL: str = "llama3.2"
    _DEFAULT_TIMEOUT: int = 2

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialise le provider avec le serveur et le modèle par défaut."""
        self._host = (host or self._DEFAULT_HOST).rstrip("/")
        self._model = model or self._DEFAULT_MODEL
        self._timeout = timeout or self._DEFAULT_TIMEOUT

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "ollama"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la capacité de génération de résumés."""
        return [RuntimeCapability.SUMMARIZATION]

    @property
    def host(self) -> str:
        """Retourne l'hôte configuré."""
        return self._host

    @property
    def model(self) -> str:
        """Retourne le modèle configuré."""
        return self._model

    def is_ollama_present(self) -> bool:
        """Indique si Ollama est installé (package Python ou binaire)."""
        if importlib.util.find_spec("ollama") is not None:
            return True
        return shutil.which("ollama") is not None

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Effectue une requête HTTP vers l'API Ollama.

        Raises:
            urllib.error.URLError: si le serveur n'est pas accessible.
            json.JSONDecodeError: si la réponse n'est pas du JSON valide.
        """
        url = f"{self._host}{path}"
        data: bytes | None = None
        headers: dict[str, str] = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def is_server_reachable(self) -> bool:
        """Indique si le serveur Ollama répond."""
        try:
            self._request("GET", "/api/tags")
            return True
        except urllib.error.URLError:
            return False
        except Exception:  # pragma: no cover - défense large
            return False

    def get_version(self) -> RuntimeReport:
        """Récupère la version du serveur Ollama."""
        try:
            data = self._request("GET", "/api/version")
            version = data.get("version", "unknown")
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Ollama version {version}.",
                details={"host": self._host, "version": version},
            )
        except urllib.error.URLError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=f"Serveur Ollama inaccessible sur {self._host}.",
                details={"host": self._host, "error": str(exc)},
            )
        except Exception as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Erreur lors de la récupération de la version : {exc}.",
                details={"host": self._host, "error": str(exc)},
            )

    def _fetch_tags(self) -> list[str]:
        """Récupère la liste des modèles disponibles auprès du serveur Ollama.

        Raises:
            urllib.error.URLError: si le serveur n'est pas accessible.
        """
        data = self._request("GET", "/api/tags")
        models = data.get("models", [])
        return [
            str(model.get("name", ""))
            for model in models
            if isinstance(model, dict)
        ]

    def list_installed_models(self) -> RuntimeReport:
        """Liste les modèles installés sur le serveur Ollama."""
        try:
            tags = self._fetch_tags()
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"{len(tags)} modèle(s) installé(s).",
                details={"host": self._host, "models": sorted(tags)},
            )
        except urllib.error.URLError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=f"Serveur Ollama inaccessible sur {self._host}.",
                details={"host": self._host, "error": str(exc)},
            )
        except Exception as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Erreur lors de la récupération des modèles : {exc}.",
                details={"host": self._host, "error": str(exc)},
            )

    def is_model_available(self, model_name: str | None = None) -> RuntimeReport:
        """Vérifie qu'un modèle est installé sur le serveur."""
        model = model_name or self._model
        report = self.list_installed_models()
        if report.status != RuntimeStatus.HEALTHY:
            return report

        installed = report.details.get("models", [])
        if model in installed:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Le modèle '{model}' est installé.",
                details={"host": self._host, "model": model},
            )

        return RuntimeReport(
            provider_name=self.name,
            status=RuntimeStatus.MISSING,
            capabilities=self.capabilities,
            message=f"Le modèle '{model}' n'est pas installé.",
            details={"host": self._host, "model": model, "installed_models": installed},
        )

    def install_model(self, model_name: str | None = None) -> RuntimeReport:
        """Télécharge un modèle auprès du serveur Ollama."""
        model = model_name or self._model
        try:
            self._request(
                "POST",
                "/api/pull",
                payload={"name": model, "stream": False},
            )
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Modèle '{model}' installé avec succès.",
                details={"host": self._host, "model": model},
            )
        except urllib.error.URLError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec du téléchargement du modèle '{model}' : {exc}.",
                details={"host": self._host, "model": model, "error": str(exc)},
            )
        except Exception as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec du téléchargement du modèle '{model}' : {exc}.",
                details={"host": self._host, "model": model, "error": str(exc)},
            )

    def remove_model(self, model_name: str | None = None) -> RuntimeReport:
        """Supprime un modèle du serveur Ollama."""
        model = model_name or self._model
        try:
            self._request(
                "DELETE",
                "/api/delete",
                payload={"name": model},
            )
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Modèle '{model}' supprimé avec succès.",
                details={"host": self._host, "model": model},
            )
        except urllib.error.URLError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec de la suppression du modèle '{model}' : {exc}.",
                details={"host": self._host, "model": model, "error": str(exc)},
            )
        except Exception as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec de la suppression du modèle '{model}' : {exc}.",
                details={"host": self._host, "model": model, "error": str(exc)},
            )

    def generate(self, prompt: str, model_name: str | None = None) -> RuntimeReport:
        """Génère un résumé via l'API Ollama."""
        model = model_name or self._model
        try:
            data = self._request(
                "POST",
                "/api/generate",
                payload={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response = data.get("response", "")
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message="Réponse Ollama reçue.",
                details={
                    "host": self._host,
                    "model": model,
                    "response": response,
                },
            )
        except urllib.error.URLError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=f"Serveur Ollama inaccessible sur {self._host}.",
                details={"host": self._host, "model": model, "error": str(exc)},
            )
        except Exception as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec de la génération Ollama : {exc}.",
                details={"host": self._host, "model": model, "error": str(exc)},
            )

    def status(self) -> RuntimeStatus:
        """Évalue rapidement l'état d'Ollama."""
        if not self.is_ollama_present():
            return RuntimeStatus.MISSING
        try:
            tags = self._fetch_tags()
        except urllib.error.URLError:
            return RuntimeStatus.MISSING
        except Exception:  # pragma: no cover - défense large
            return RuntimeStatus.ERROR

        if self._model in tags:
            return RuntimeStatus.HEALTHY
        return RuntimeStatus.DEGRADED

    def diagnose(self) -> RuntimeReport:
        """Diagnostique complet du serveur Ollama et du modèle configuré."""
        package_available = self.is_ollama_present()
        version_report = self.get_version()
        models_report = self.list_installed_models()
        model_report = self.is_model_available()

        if not package_available:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message="Ollama n'est pas installé.",
                details={
                    "host": self._host,
                    "model": self._model,
                    "package_installed": False,
                    "version_report": version_report.details,
                    "installed_models": models_report.details.get("models", []),
                    "model_report": model_report.details,
                },
            )

        if version_report.status != RuntimeStatus.HEALTHY:
            return RuntimeReport(
                provider_name=self.name,
                status=version_report.status,
                capabilities=self.capabilities,
                message=version_report.message,
                details={
                    "host": self._host,
                    "model": self._model,
                    "package_installed": package_available,
                    "version_report": version_report.details,
                    "installed_models": models_report.details.get("models", []),
                    "model_report": model_report.details,
                },
            )

        final_status = model_report.status
        if final_status == RuntimeStatus.HEALTHY:
            message = (
                f"Ollama {version_report.details.get('version')} est disponible "
                f"et le modèle '{self._model}' est installé."
            )
        else:
            message = (
                f"Ollama {version_report.details.get('version')} est disponible "
                f"mais le modèle '{self._model}' n'est pas installé."
            )

        return RuntimeReport(
            provider_name=self.name,
            status=final_status,
            capabilities=self.capabilities,
            message=message,
            details={
                "host": self._host,
                "model": self._model,
                "package_installed": package_available,
                "version": version_report.details.get("version"),
                "installed_models": models_report.details.get("models", []),
                "model_report": model_report.details,
            },
        )

    def suggested_actions(self, report: RuntimeReport) -> list[RuntimeAction]:
        """Propose des actions selon l'état d'Ollama et du modèle."""
        if report.status == RuntimeStatus.HEALTHY:
            return []

        if not self.is_ollama_present():
            return [
                RuntimeAction(
                    action_type=RuntimeActionType.INSTALL_PACKAGE,
                    provider_name=self.name,
                    message="Installer Ollama.",
                    description="Le package ou le binaire Ollama n'est pas installé.",
                    available=False,
                    requires_user=True,
                    parameters={"host": self._host},
                )
            ]

        if not self.is_server_reachable():
            return [
                RuntimeAction(
                    action_type=RuntimeActionType.START_SERVER,
                    provider_name=self.name,
                    message="Démarrer le serveur Ollama.",
                    description=f"Le serveur Ollama sur {self._host} ne répond pas.",
                    available=self.can_start_server(),
                    requires_user=True,
                    parameters={"host": self._host},
                )
            ]

        if report.status in (RuntimeStatus.MISSING, RuntimeStatus.DEGRADED):
            return [
                RuntimeAction(
                    action_type=RuntimeActionType.DOWNLOAD_MODEL,
                    provider_name=self.name,
                    message=f"Télécharger le modèle Ollama '{self._model}'.",
                    description=f"Le modèle '{self._model}' n'est pas installé sur le serveur.",
                    available=self.can_install(),
                    requires_user=True,
                    parameters={
                        "host": self._host,
                        "model": self._model,
                    },
                )
            ]

        return super().suggested_actions(report)

    def can_install(self) -> bool:
        """L'installation d'un modèle est possible si le serveur est joignable."""
        return self.is_ollama_present() and self.is_server_reachable()

    def can_start_server(self) -> bool:
        """Le serveur peut être démarré si Ollama est installé mais non joignable."""
        return self.is_ollama_present() and not self.is_server_reachable()

    def start_server(self) -> RuntimeReport:
        """Démarre le serveur Ollama en arrière-plan."""
        if not self.is_ollama_present():
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message="Ollama n'est pas installé.",
                details={"host": self._host},
            )

        if self.is_server_reachable():
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message="Le serveur Ollama est déjà actif.",
                details={"host": self._host},
            )

        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Échec du démarrage du serveur Ollama : {exc}.",
                details={"host": self._host, "error": str(exc)},
            )

        for _ in range(30):
            time.sleep(0.5)
            if self.is_server_reachable():
                return RuntimeReport(
                    provider_name=self.name,
                    status=RuntimeStatus.HEALTHY,
                    capabilities=self.capabilities,
                    message="Serveur Ollama démarré avec succès.",
                    details={"host": self._host},
                )

        return RuntimeReport(
            provider_name=self.name,
            status=RuntimeStatus.ERROR,
            capabilities=self.capabilities,
            message="Le serveur Ollama n'a pas répondu dans le délai imparti.",
            details={"host": self._host},
        )

    def install(self) -> RuntimeReport:
        """Installe le modèle configuré."""
        return self.install_model(self._model)

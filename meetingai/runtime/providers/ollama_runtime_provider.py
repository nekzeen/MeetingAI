"""Provider Runtime pour Ollama."""

from __future__ import annotations

import importlib.util
import json
import urllib.error
import urllib.request

from meetingai.runtime.runtime_capability import RuntimeCapability
from meetingai.runtime.runtime_provider import RuntimeProvider
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class OllamaRuntimeProvider(RuntimeProvider):
    """Vérifie la disponibilité du serveur Ollama.

    Ce provider ne modifie jamais le système. Il tente d'interroger l'API
    locale d'Ollama (par défaut http://localhost:11434) et retourne un rapport
    décrivant l'état du serveur.
    """

    _DEFAULT_HOST = "http://localhost:11434"

    @property
    def name(self) -> str:
        """Retourne le nom du provider."""
        return "ollama"

    @property
    def capabilities(self) -> list[RuntimeCapability]:
        """Retourne la capacité de génération de résumés."""
        return [RuntimeCapability.SUMMARIZATION]

    def _has_ollama_package(self) -> bool:
        """Indique si le package Python ollama est installé."""
        return importlib.util.find_spec("ollama") is not None

    def status(self) -> RuntimeStatus:
        """Évalue rapidement l'état d'Ollama."""
        try:
            self._fetch_tags()
            return RuntimeStatus.HEALTHY
        except urllib.error.URLError:
            return RuntimeStatus.MISSING
        except Exception:  # pragma: no cover - défense large
            return RuntimeStatus.ERROR

    def diagnose(self) -> RuntimeReport:
        """Diagnostique le serveur Ollama local."""
        host = self._DEFAULT_HOST
        package_available = self._has_ollama_package()

        try:
            tags = self._fetch_tags()
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.HEALTHY,
                capabilities=self.capabilities,
                message=f"Serveur Ollama accessible sur {host}.",
                details={
                    "host": host,
                    "package_installed": package_available,
                    "models": tags,
                },
            )
        except urllib.error.URLError as exc:
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.MISSING,
                capabilities=self.capabilities,
                message=f"Aucun serveur Ollama détecté sur {host}.",
                details={
                    "host": host,
                    "package_installed": package_available,
                    "error": str(exc),
                },
            )
        except Exception as exc:  # pragma: no cover - défense large
            return RuntimeReport(
                provider_name=self.name,
                status=RuntimeStatus.ERROR,
                capabilities=self.capabilities,
                message=f"Erreur lors du diagnostic Ollama : {exc}.",
                details={
                    "host": host,
                    "package_installed": package_available,
                    "error": str(exc),
                },
            )

    def _fetch_tags(self) -> list[str]:
        """Récupère la liste des modèles disponibles auprès du serveur Ollama.

        Raises:
            urllib.error.URLError: si le serveur n'est pas accessible.
        """
        request = urllib.request.Request(
            f"{self._DEFAULT_HOST}/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = data.get("models", [])
            return [model.get("name", "") for model in models if model]

    def can_install(self) -> bool:
        """L'installation automatique d'Ollama n'est pas supportée."""
        return False

    def install(self) -> RuntimeReport:
        """Renvoie un rapport indiquant que l'installation n'est pas supportée."""
        return RuntimeReport(
            provider_name=self.name,
            status=self.status(),
            capabilities=self.capabilities,
            message="Installation automatique d'Ollama non supportée.",
            details={},
        )

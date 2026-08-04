"""Composition racine de l'application MeetingAI.

Ce module regroupe l'instanciation des composants centraux de l'application :
configuration, journalisation, registre de services et gestionnaire d'actions.
Il constitue le point d'entrée unique de l'injection de dépendances.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from meetingai.config.config_manager import ConfigManager
from meetingai.controllers.export_controller import ExportController
from meetingai.controllers.media_controller import MediaController
from meetingai.controllers.pipeline_controller import PipelineController
from meetingai.controllers.runtime_controller import RuntimeController
from meetingai.controllers.summarization_controller import (
    SummarizationController,
)
from meetingai.controllers.transcription_controller import TranscriptionController
from meetingai.services.export.export_service import ExportService
from meetingai.services.summarization.summarization_factory import (
    SummarizationFactory,
)
from meetingai.core.service_registry import ServiceRegistry
from meetingai.core.task_manager import TaskManager
from meetingai.core.worker_manager import WorkerManager
from meetingai.services.model_manager import ModelManager
from meetingai.gui.action_manager import ActionManager
from meetingai.logging.logger_manager import LoggerManager
from meetingai.services.media_service import MediaService
from meetingai.services.speech_to_text.speech_to_text_factory import (
    SpeechToTextFactory,
)


class ApplicationContext:
    """Conteneur racine des composants partagés de MeetingAI.

    Cette classe crée et expose les instances uniques de ``ConfigManager``,
    ``LoggerManager``, ``ServiceRegistry`` et ``ActionManager``. Elle
    enregistre automatiquement ces composants dans le ``ServiceRegistry``
    afin de préparer l'injection de dépendances futures.

    Args:
        config_path: Chemin du fichier de configuration JSON. Par défaut,
            ``config/config.json``.
        logs_dir: Répertoire des fichiers de journalisation. Par défaut,
            le dossier ``logs`` à la racine du projet.
    """

    def __init__(
        self,
        config_path: str | Path = "config/config.json",
        logs_dir: str | Path = "logs",
    ) -> None:
        """Initialise les composants centraux de l'application."""
        self.config: ConfigManager = ConfigManager(config_path=config_path)
        self.logger: LoggerManager = LoggerManager(
            config_manager=self.config, logs_dir=logs_dir
        )
        self.service_registry: ServiceRegistry = ServiceRegistry()
        self.action_manager: ActionManager = ActionManager()
        self.media_service: MediaService = MediaService()
        self.task_manager: TaskManager = TaskManager()
        self.speech_to_text_factory: SpeechToTextFactory = SpeechToTextFactory()
        self.speech_to_text_service = self.speech_to_text_factory.create(
            self.config.speech_to_text
        )
        self.media_controller: MediaController = MediaController(
            media_service=self.media_service,
            logger_manager=self.logger,
        )
        self.model_manager: ModelManager = ModelManager()
        self.worker_manager: WorkerManager = WorkerManager()
        self.transcription_controller: TranscriptionController = (
            TranscriptionController(
                speech_to_text_service=self.speech_to_text_service,
                task_manager=self.task_manager,
                worker_manager=self.worker_manager,
                logger_manager=self.logger,
            )
        )
        self.export_service: ExportService = ExportService()
        self.export_controller: ExportController = ExportController(
            export_service=self.export_service,
            config_manager=self.config,
        )
        self.summarization_factory: SummarizationFactory = SummarizationFactory()
        self.summarization_controller: SummarizationController = (
            SummarizationController(
                factory=self.summarization_factory,
                config_manager=self.config,
            )
        )
        self.pipeline_controller: PipelineController = PipelineController(
            transcription_controller=self.transcription_controller,
            summarization_controller=self.summarization_controller,
            export_controller=self.export_controller,
        )
        self.runtime_controller: RuntimeController = RuntimeController()
        self.transcription_controller.transcription_ready.connect(
            self.export_controller.on_transcription_ready
        )
        self.transcription_controller.transcription_ready.connect(
            self.summarization_controller.on_transcription_ready
        )
        self._register_components()

    def _register_components(self) -> None:
        """Enregistre les composants partagés dans le registre de services."""
        self.service_registry.register("config_manager", self.config)
        self.service_registry.register("logger_manager", self.logger)
        self.service_registry.register("action_manager", self.action_manager)
        self.service_registry.register("media_service", self.media_service)
        self.service_registry.register("media_controller", self.media_controller)
        self.service_registry.register(
            "transcription_controller", self.transcription_controller
        )
        self.service_registry.register("task_manager", self.task_manager)
        self.service_registry.register(
            "speech_to_text_service",
            self.speech_to_text_service,
        )
        self.service_registry.register(
            "speech_to_text_factory", self.speech_to_text_factory
        )
        self.service_registry.register("model_manager", self.model_manager)
        self.service_registry.register("worker_manager", self.worker_manager)
        self.service_registry.register("export_service", self.export_service)
        self.service_registry.register(
            "export_controller", self.export_controller
        )
        self.service_registry.register(
            "summarization_factory", self.summarization_factory
        )
        self.service_registry.register(
            "summarization_controller", self.summarization_controller
        )
        self.service_registry.register(
            "pipeline_controller", self.pipeline_controller
        )
        self.service_registry.register(
            "runtime_controller", self.runtime_controller
        )

    def get_service(self, name: str) -> Any:
        """Retourne un service enregistré dans le registre.

        Args:
            name: Clé du service demandé.

        Returns:
            Instance du service enregistrée.

        Raises:
            KeyError: Si le service n'est pas enregistré.
        """
        return self.service_registry.get(name)

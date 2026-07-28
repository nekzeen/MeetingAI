"""Contrôleur de sélection et d'ouverture des médias."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox

from meetingai.logging.logger_manager import LoggerManager
from meetingai.models.media_file import MediaFile
from meetingai.services.media_service import MediaService


class MediaController(QObject):
    """Orchestre la sélection d'un fichier média et son chargement.

    Ce contrôleur affiche une boîte de dialogue de sélection, valide le fichier
    via ``MediaService`` et conserve le média courant.

    Aucune logique de transcription ni de traitement audio n'est implémentée
    ici.

    Args:
        media_service: Service de gestion des fichiers médias.
        logger_manager: Gestionnaire de logs de l'application.
        parent: Widget parent optionnel pour les boîtes de dialogue.
    """

    media_loaded = Signal(object)

    def __init__(
        self,
        media_service: MediaService,
        logger_manager: LoggerManager,
        parent: object | None = None,
    ) -> None:
        """Initialise le contrôleur média."""
        super().__init__(parent)
        self._media_service = media_service
        self._logger = logger_manager.get_logger(__name__)
        self._parent = parent
        self._current_media: MediaFile | None = None

    @property
    def current_media(self) -> MediaFile | None:
        """Retourne le média actuellement sélectionné.

        Returns:
            Instance ``MediaFile`` ou ``None`` si aucun média n'est chargé.
        """
        return self._current_media

    def open_media(self) -> None:
        """Ouvre la boîte de dialogue de sélection et charge le média choisi."""
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self._parent,
            "Ouvrir un média",
            "",
            self._build_file_filter(),
        )

        if not file_path:
            return

        try:
            self._current_media = self._media_service.open(file_path)
            self._logger.info("Média ouvert : %s", self._current_media.path)
            self.media_loaded.emit(self._current_media)
        except (FileNotFoundError, IsADirectoryError, ValueError) as exc:
            self._logger.error("Échec de l'ouverture du média : %s", exc)
            QMessageBox.critical(
                self._parent,
                "Erreur lors de l'ouverture",
                str(exc),
            )

    def transcribe_current_media(self) -> None:
        """Méthode obsolète : la transcription est gérée par ``TranscriptionController``.

        Conserve temporairement une interface stable pour les appelants
        existants afin d'éviter une rupture immédiate.
        """
        raise NotImplementedError(
            "Utilisez TranscriptionController.transcribe() pour lancer une transcription."
        )

    def _build_file_filter(self) -> str:
        """Construit le filtre de formats supportés pour QFileDialog."""
        audio_formats = " ".join(
            f"*{ext}" for ext in sorted(MediaService.AUDIO_EXTENSIONS)
        )
        video_formats = " ".join(
            f"*{ext}" for ext in sorted(MediaService.VIDEO_EXTENSIONS)
        )
        return (
            f"Audio ({audio_formats});;"
            f"Vidéo ({video_formats});;"
            "Tous les fichiers (*.*)"
        )

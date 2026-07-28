"""Conteneur principal des vues de l'application MeetingAI."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from meetingai.controllers.media_controller import MediaController
from meetingai.core.service_registry import ServiceRegistry
from meetingai.gui.widgets.history_widget import HistoryWidget
from meetingai.gui.widgets.media_information_widget import MediaInformationWidget
from meetingai.gui.widgets.summary_widget import SummaryWidget
from meetingai.gui.widgets.transcript_widget import TranscriptWidget


class Workspace(QWidget):
    """Widget central contenant le layout principal de l'application.

    Le ``Workspace`` accueille les panneaux de l'interface graphique. Il
    utilise un ``QHBoxLayout`` horizontal afin de faciliter l'ajout de
    plusieurs vues côte à côte.

    Ce composant intègre ``MediaInformationWidget`` et le connecte au
    contrôleur média afin d'afficher automatiquement les informations du
    média chargé.
    """

    _MARGIN: int = 12
    _SPACING: int = 12
    _LEFT_RATIO: float = 0.30
    _RIGHT_RATIO: float = 0.70
    _DEFAULT_WIDTH: int = 1200

    def __init__(
        self,
        parent: QWidget | None = None,
        media_controller: MediaController | None = None,
    ) -> None:
        """Initialise le workspace et ses panneaux.

        Args:
            parent: Widget parent éventuel.
            media_controller: Contrôleur média dont le signal
                ``media_loaded`` mettra à jour le widget d'information. S'il
                n'est pas fourni, le workspace tente de le récupérer depuis le
                ``ServiceRegistry``.
        """
        super().__init__(parent)
        self._setup_ui()
        self._connect_controller(media_controller)

    def _setup_ui(self) -> None:
        """Crée le splitter horizontal et organise les panneaux."""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(
            self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN
        )
        self._layout.setSpacing(self._SPACING)

        self._info_widget = MediaInformationWidget(self)
        self._history_widget = HistoryWidget(self)
        self._transcript_widget = TranscriptWidget(self)
        self._summary_widget = SummaryWidget(self)

        left_panel = self._build_column(
            self._info_widget,
            self._history_widget,
        )
        right_panel = self._build_column(
            self._transcript_widget,
            self._summary_widget,
        )

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.addWidget(left_panel)
        self._splitter.addWidget(right_panel)
        self._splitter.setSizes(
            [
                int(self._DEFAULT_WIDTH * self._LEFT_RATIO),
                int(self._DEFAULT_WIDTH * self._RIGHT_RATIO),
            ]
        )

        self._layout.addWidget(self._splitter)

    def _build_column(self, *widgets: QWidget) -> QWidget:
        """Construit une colonne verticale contenant les widgets donnés."""
        column = QWidget(self)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(self._SPACING)
        for widget in widgets:
            column_layout.addWidget(widget)
        return column

    def _connect_controller(self, media_controller: MediaController | None) -> None:
        """Connecte le signal ``media_loaded`` au widget d'information."""
        if media_controller is None:
            try:
                media_controller = ServiceRegistry().get("media_controller")
            except KeyError:
                return
        media_controller.media_loaded.connect(self._info_widget.set_media)

    def layout(self) -> QHBoxLayout:
        """Retourne le layout principal du workspace.

        Returns:
            Le ``QHBoxLayout`` du workspace.
        """
        return self._layout

    @property
    def media_information_widget(self) -> MediaInformationWidget:
        """Retourne le widget d'information du média."""
        return self._info_widget

    @property
    def history_widget(self) -> HistoryWidget:
        """Retourne le panneau d'historique."""
        return self._history_widget

    @property
    def transcript_widget(self) -> TranscriptWidget:
        """Retourne le panneau de transcription."""
        return self._transcript_widget

    @property
    def summary_widget(self) -> SummaryWidget:
        """Retourne le panneau de résumé IA."""
        return self._summary_widget

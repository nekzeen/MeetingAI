"""Conteneur principal des vues de l'application MeetingAI."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from meetingai.controllers.media_controller import MediaController
from meetingai.controllers.summarization_controller import (
    SummarizationController,
)
from meetingai.controllers.transcription_controller import TranscriptionController
from meetingai.core.service_registry import ServiceRegistry
from meetingai.gui.widgets.history_widget import HistoryWidget
from meetingai.gui.widgets.media_information_widget import MediaInformationWidget
from meetingai.gui.widgets.summary_widget import SummaryWidget
from meetingai.gui.widgets.transcript_widget import TranscriptWidget


class WelcomeWidget(QWidget):
    """Écran d'accueil affiché lorsqu'aucun média n'est ouvert."""

    open_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise l'écran d'accueil."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construit le contenu de l'accueil."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)

        title = QLabel("Bienvenue dans MeetingAI", self)
        title.setObjectName("welcome_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Ouvrez un média pour transcrire, résumer et exporter votre réunion.",
            self,
        )
        subtitle.setObjectName("welcome_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #6c757d;")
        layout.addWidget(subtitle)

        open_button = QPushButton("Ouvrir un média", self)
        open_button.setObjectName("welcome_open_button")
        open_button.setStyleSheet(
            "QPushButton { font-size: 16px; padding: 12px 24px; }"
        )
        open_button.clicked.connect(self.open_requested.emit)
        layout.addWidget(open_button, 0, Qt.AlignmentFlag.AlignCenter)

        steps = QLabel(
            "1. Ouvrir  →  2. Transcrire  →  3. Résumer  →  4. Exporter",
            self,
        )
        steps.setObjectName("welcome_steps")
        steps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        steps.setStyleSheet("font-size: 14px; color: #6c757d;")
        layout.addWidget(steps)


class _EditorWidget(QWidget):
    """Zone d'édition principale affichant média, transcription et résumé."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise la zone d'édition."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construit le splitter principal : panneau latéral + zone centrale."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([280, 920])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setHandleWidth(8)
        main_layout.addWidget(splitter)

    def _build_left_panel(self) -> QWidget:
        """Panneau latéral avec informations média et historique."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(12)

        self._info_widget = MediaInformationWidget(panel)
        layout.addWidget(self._info_widget)

        self._history_widget = HistoryWidget(panel)
        layout.addWidget(self._history_widget)

        layout.addStretch()
        return panel

    def _build_right_panel(self) -> QWidget:
        """Panneau central avec transcription et résumé."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(8)

        self._transcript_widget = TranscriptWidget(panel)
        self._summary_widget = SummaryWidget(panel)

        splitter = QSplitter(Qt.Orientation.Vertical, panel)
        splitter.addWidget(self._transcript_widget)
        splitter.addWidget(self._summary_widget)
        splitter.setSizes([525, 225])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        splitter.setHandleWidth(8)

        layout.addWidget(splitter)
        return panel


class Workspace(QWidget):
    """Widget central contenant le layout principal de l'application.

    Le ``Workspace`` affiche un écran d'accueil lorsqu'aucun média n'est
    ouvert, puis bascule vers une zone d'édition centrée sur la transcription.
    """

    _MARGIN: int = 12
    _SPACING: int = 12

    def __init__(
        self,
        parent: QWidget | None = None,
        media_controller: MediaController | None = None,
        transcription_controller: TranscriptionController | None = None,
        summarization_controller: SummarizationController | None = None,
    ) -> None:
        """Initialise le workspace et ses panneaux."""
        super().__init__(parent)
        self._setup_ui()
        self._connect_controllers(
            media_controller,
            transcription_controller,
            summarization_controller,
        )

    def _setup_ui(self) -> None:
        """Construit l'écran d'accueil puis l'éditeur."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN
        )
        main_layout.setSpacing(self._SPACING)

        self._stack = QStackedWidget(self)
        self._welcome = WelcomeWidget(self)
        self._editor = _EditorWidget(self)

        self._stack.addWidget(self._welcome)
        self._stack.addWidget(self._editor)
        main_layout.addWidget(self._stack)

    def _connect_controllers(
        self,
        media_controller: MediaController | None,
        transcription_controller: TranscriptionController | None,
        summarization_controller: SummarizationController | None,
    ) -> None:
        """Connecte les signaux des contrôleurs aux widgets concernés."""
        if media_controller is None:
            try:
                media_controller = ServiceRegistry().get("media_controller")
            except KeyError:
                return
        media_controller.media_loaded.connect(self._on_media_loaded)
        media_controller.media_loaded.connect(
            self._editor._info_widget.set_media
        )
        if hasattr(media_controller, "open_media"):
            self._welcome.open_requested.connect(media_controller.open_media)

        if transcription_controller is None:
            try:
                transcription_controller = ServiceRegistry().get(
                    "transcription_controller"
                )
            except KeyError:
                return
        transcription_controller.transcription_ready.connect(
            self._editor._transcript_widget.set_transcription
        )

        if summarization_controller is None:
            try:
                summarization_controller = ServiceRegistry().get(
                    "summarization_controller"
                )
            except KeyError:
                return
        summarization_controller.summary_ready.connect(
            self._editor._summary_widget.set_summary
        )

    def _on_media_loaded(self, _media: object | None = None) -> None:
        """Passe à l'éditeur lorsqu'un média est ouvert."""
        self._stack.setCurrentIndex(1)

    @property
    def media_information_widget(self) -> MediaInformationWidget:
        """Retourne le widget d'information du média."""
        return self._editor._info_widget

    @property
    def history_widget(self) -> HistoryWidget:
        """Retourne le panneau d'historique."""
        return self._editor._history_widget

    @property
    def transcript_widget(self) -> TranscriptWidget:
        """Retourne le panneau de transcription."""
        return self._editor._transcript_widget

    @property
    def summary_widget(self) -> SummaryWidget:
        """Retourne le panneau de résumé IA."""
        return self._editor._summary_widget

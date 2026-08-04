"""Fenêtre principale de MeetingAI."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QToolBar,
    QWidget,
)

from meetingai.controllers.settings_controller import SettingsController
from meetingai.core.application_context import ApplicationContext
from meetingai.gui.action_manager import ActionManager
from meetingai.gui.runtime_window import RuntimeWindow
from meetingai.gui.settings_window import SettingsWindow
from meetingai.gui.workspace import Workspace
from meetingai.services.speech_to_text.transcription_result import (
    TranscriptionResult,
)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application MeetingAI.

    Cette fenêtre constitue le squelette de l'interface graphique. Elle
    contient une barre de menus, une barre d'outils vide, une barre de statut
    et une zone centrale vide, prêtes à accueillir les futures fonctionnalités.

    Aucun widget métier, aucune action et aucun raccourci clavier ne sont
    définis ici.
    """

    DEFAULT_WIDTH: int = 1200
    DEFAULT_HEIGHT: int = 800

    def __init__(
        self,
        parent: QWidget | None = None,
        context: ApplicationContext | None = None,
    ) -> None:
        """Initialise la fenêtre principale.

        Args:
            parent: Widget parent éventuel.
            context: Contexte applicatif racine. S'il est fourni, la fenêtre
                assemble les composants à partir de celui-ci.
        """
        super().__init__(parent)
        self._context = context
        self.setWindowTitle("MeetingAI")
        self._setup_ui()
        self._center_on_screen()

    def _setup_ui(self) -> None:
        """Construit le squelette de l'interface graphique."""
        self._action_manager = (
            self._context.action_manager if self._context else ActionManager(self)
        )
        self.setCentralWidget(
            Workspace(
                self,
                media_controller=self._context.media_controller
                if self._context
                else None,
                transcription_controller=self._context.transcription_controller
                if self._context
                else None,
                summarization_controller=self._context.summarization_controller
                if self._context
                else None,
            )
        )
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_status_bar()
        if self._context is not None:
            self._action_manager.connect_open_media(self._context.media_controller)
            self._action_manager.connect_transcribe(
                lambda: self._context.transcription_controller.transcribe(
                    self._context.media_controller.current_media
                )
            )
            self._action_manager.preferences_action.triggered.connect(
                self._open_settings
            )
            if self._context.runtime_controller is not None:
                self._action_manager.runtime_action.triggered.connect(
                    self._open_runtime_window
                )
            if self._context.export_controller is not None:
                self._action_manager.export_txt_action.triggered.connect(
                    self._context.export_controller.export_txt
                )
                self._action_manager.export_markdown_action.triggered.connect(
                    self._context.export_controller.export_markdown
                )
            if self._context.summarization_controller is not None:
                self._action_manager.summarize_action.triggered.connect(
                    self._context.summarization_controller.summarize_current_transcription
                )
            if self._context.pipeline_controller is not None:
                self._action_manager.connect_pipeline(
                    lambda: self._context.pipeline_controller.start(
                        self._context.media_controller.current_media
                    )
                )
            if self._context.transcription_controller is not None:
                self._context.transcription_controller.transcription_status.connect(
                    self._show_transcription_status
                )
                self._context.transcription_controller.transcription_ready.connect(
                    self._on_transcription_ready
                )
                self._context.transcription_controller.transcription_failed.connect(
                    self._show_transcription_error
                )
            if self._context.pipeline_controller is not None:
                self._context.pipeline_controller.pipeline_failed.connect(
                    self._show_pipeline_error
                )

    def _on_transcription_ready(self, result: TranscriptionResult) -> None:
        """Affiche un avertissement si la transcription a utilisé le fallback CPU."""
        self._progress_bar.setVisible(False)
        warning = result.metadata.get("warning")
        if warning:
            QMessageBox.information(
                self,
                "Mode CPU utilisé",
                warning,
            )

    def _show_transcription_status(self, message: str) -> None:
        """Affiche le message de phase de transcription et active la progression."""
        self.statusBar().showMessage(message)
        self._progress_bar.setVisible(True)

    def _show_transcription_error(self, message: str) -> None:
        """Affiche une boîte de dialogue en cas d'échec de transcription."""
        self._progress_bar.setVisible(False)
        QMessageBox.critical(
            self,
            "Erreur de transcription",
            message,
        )

    def _show_pipeline_error(self, message: str) -> None:
        """Affiche une boîte de dialogue en cas d'échec du pipeline."""
        self._progress_bar.setVisible(False)
        QMessageBox.critical(
            self,
            "Erreur du pipeline",
            message,
        )

    def _open_runtime_window(self) -> None:
        """Ouvre la fenêtre d'état du système."""
        if self._context is None:
            return
        dialog = RuntimeWindow(
            runtime_controller=self._context.runtime_controller,
            parent=self,
        )
        dialog.exec()

    def _open_settings(self) -> None:
        """Ouvre la fenêtre de paramètres et persiste les modifications."""
        if self._context is None:
            return

        controller = SettingsController(
            self._context.config,
            self._context.speech_to_text_factory,
            self._context.summarization_factory,
        )
        dialog = SettingsWindow(
            initial_settings=controller.load_settings(),
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            controller.save_settings(dialog.get_settings())

    def _setup_menu_bar(self) -> None:
        """Construit la barre de menus à partir de l'ActionManager."""
        menu_bar: QMenuBar = self.menuBar()
        actions = self._action_manager.actions

        file_menu = QMenu("Fichier", self)
        menu_bar.addMenu(file_menu)
        file_menu.addAction(actions["new"])
        file_menu.addAction(actions["open"])
        file_menu.addAction(actions["save"])
        file_menu.addSeparator()
        file_menu.addAction(actions["export_txt"])
        file_menu.addAction(actions["export_markdown"])
        file_menu.addSeparator()
        file_menu.addAction(actions["quit"])

        menu_bar.addMenu(QMenu("Édition", self))

        tools_menu = QMenu("Outils", self)
        menu_bar.addMenu(tools_menu)
        tools_menu.addAction(actions["transcribe"])
        tools_menu.addAction(actions["summarize"])
        tools_menu.addAction(actions["pipeline"])
        tools_menu.addSeparator()
        tools_menu.addAction(actions["runtime"])
        tools_menu.addSeparator()
        tools_menu.addAction(actions["preferences"])

        menu_bar.addMenu(QMenu("Affichage", self))

        help_menu = QMenu("Aide", self)
        menu_bar.addMenu(help_menu)
        help_menu.addAction(actions["about"])

    def _setup_tool_bar(self) -> None:
        """Ajoute une barre d'outils avec les actions du workflow."""
        tool_bar = self.addToolBar("Principal")
        tool_bar.setObjectName("main_tool_bar")
        tool_bar.setMovable(False)
        tool_bar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        actions = self._action_manager.actions
        tool_bar.addAction(actions["open"])
        tool_bar.addAction(actions["transcribe"])
        tool_bar.addAction(actions["summarize"])
        tool_bar.addAction(actions["export_markdown"])

    def _setup_status_bar(self) -> None:
        """Construit la barre de statut avec les fournisseurs et la progression."""
        status_bar = QStatusBar(self)
        status_bar.setObjectName("main_status_bar")
        self.setStatusBar(status_bar)

        self._runtime_status_label = QLabel("Runtime : —", self)
        self._runtime_status_label.setObjectName("runtime_status_label")
        status_bar.addWidget(self._runtime_status_label)

        self._stt_provider_label = QLabel("STT : —", self)
        self._stt_provider_label.setObjectName("stt_provider_label")
        status_bar.addWidget(self._stt_provider_label)

        self._ia_provider_label = QLabel("IA : —", self)
        self._ia_provider_label.setObjectName("ia_provider_label")
        status_bar.addWidget(self._ia_provider_label)

        status_bar.addPermanentWidget(QWidget(self), stretch=1)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setObjectName("progress_bar")
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumWidth(120)
        status_bar.addPermanentWidget(self._progress_bar)

        self._update_status_bar()

    def _update_status_bar(self) -> None:
        """Rafraîchit les fournisseurs affichés dans la barre de statut."""
        if self._context is None:
            return
        runtime = self._context.runtime_controller
        status = runtime.status()
        self._runtime_status_label.setText(f"Runtime : {status.name}")
        for name in ("whisper", "ollama"):
            report = runtime.report_for(name)
            text = "—"
            if report is not None:
                text = f"{report.provider_name} ({report.status.name})"
            if name == "whisper":
                self._stt_provider_label.setText(f"STT : {text}")
            else:
                self._ia_provider_label.setText(f"IA : {text}")

    def _show_transcription_status(self, message: str) -> None:
        """Affiche le message de phase de transcription et active la progression."""
        self.statusBar().showMessage(message)
        self._progress_bar.setVisible(True)

    def _center_on_screen(self) -> None:
        """Centre la fenêtre sur l'écran principal."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
            return

        available_geometry = screen.availableGeometry()
        x = available_geometry.center().x() - self.DEFAULT_WIDTH // 2
        y = available_geometry.center().y() - self.DEFAULT_HEIGHT // 2
        self.setGeometry(x, y, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

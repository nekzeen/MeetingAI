"""Fenêtre d'état du Runtime de MeetingAI."""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from meetingai.controllers.runtime_controller import RuntimeController
from meetingai.runtime.runtime_action import RuntimeAction, RuntimeActionType
from meetingai.runtime.runtime_report import RuntimeReport
from meetingai.runtime.runtime_status import RuntimeStatus


class _InstallThread(QThread):
    """Thread d'installation d'un provider Runtime."""

    install_finished = Signal(RuntimeReport)

    def __init__(
        self,
        controller: RuntimeController,
        provider_name: str,
        parent: QWidget | None = None,
    ) -> None:
        """Initialise le thread avec le contrôleur cible."""
        super().__init__(parent)
        self._controller = controller
        self._provider_name = provider_name

    def run(self) -> None:
        """Exécute l'installation en arrière-plan."""
        report = self._controller.install(self._provider_name)
        self.install_finished.emit(report)


class RuntimeWindow(QDialog):
    """Fenêtre affichant l'état du Runtime, les rapports et les actions proposées.

    La fenêtre s'appuie sur ``RuntimeController`` pour ne pas dupliquer la
    logique de diagnostic. Elle affiche une section dédiée à Whisper et
    permet de télécharger le modèle sélectionné depuis le provider
    ``WhisperRuntimeProvider``.

    Args:
        runtime_controller: Contrôleur fournissant les données Runtime.
        parent: Widget parent éventuel.
    """

    def __init__(
        self,
        runtime_controller: RuntimeController,
        parent: QWidget | None = None,
    ) -> None:
        """Initialise la fenêtre d'état du système."""
        super().__init__(parent)
        self.setWindowTitle("État du système")
        self._controller = runtime_controller
        self._setup_ui()
        self._refresh()

    @property
    def runtime_controller(self) -> RuntimeController:
        """Retourne le contrôleur associé."""
        return self._controller

    def _setup_ui(self) -> None:
        """Construit les sections de la fenêtre."""
        layout = QVBoxLayout(self)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("status_label")
        layout.addWidget(self._status_label)

        reports_group = QGroupBox("Diagnostics", self)
        reports_layout = QVBoxLayout(reports_group)
        self._reports_table = QTableWidget(self)
        self._reports_table.setObjectName("reports_table")
        self._reports_table.setColumnCount(3)
        self._reports_table.setHorizontalHeaderLabels(
            ["Provider", "État", "Message"]
        )
        self._reports_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._reports_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        reports_layout.addWidget(self._reports_table)
        layout.addWidget(reports_group)

        whisper_group = QGroupBox("Whisper", self)
        whisper_group.setObjectName("whisper_group")
        whisper_layout = QVBoxLayout(whisper_group)

        self._whisper_provider_label = QLabel("Provider :", self)
        self._whisper_provider_label.setObjectName("whisper_provider_label")
        whisper_layout.addWidget(self._whisper_provider_label)

        self._whisper_model_label = QLabel("Modèle :", self)
        self._whisper_model_label.setObjectName("whisper_model_label")
        whisper_layout.addWidget(self._whisper_model_label)

        self._whisper_status_label = QLabel("État :", self)
        self._whisper_status_label.setObjectName("whisper_status_label")
        whisper_layout.addWidget(self._whisper_status_label)

        self._whisper_path_label = QLabel("Emplacement :", self)
        self._whisper_path_label.setObjectName("whisper_path_label")
        self._whisper_path_label.setWordWrap(True)
        whisper_layout.addWidget(self._whisper_path_label)

        self._whisper_info_label = QLabel("Information :", self)
        self._whisper_info_label.setObjectName("whisper_info_label")
        self._whisper_info_label.setWordWrap(True)
        whisper_layout.addWidget(self._whisper_info_label)

        self._whisper_progress = QProgressBar(self)
        self._whisper_progress.setObjectName("whisper_progress")
        self._whisper_progress.setRange(0, 0)
        self._whisper_progress.setTextVisible(False)
        self._whisper_progress.setVisible(False)
        whisper_layout.addWidget(self._whisper_progress)

        self._whisper_install_button = QPushButton("Installer", self)
        self._whisper_install_button.setObjectName("whisper_install_button")
        self._whisper_install_button.setEnabled(False)
        self._whisper_install_button.clicked.connect(self._on_install_clicked)
        whisper_layout.addWidget(self._whisper_install_button)

        layout.addWidget(whisper_group)

        actions_group = QGroupBox("Actions recommandées", self)
        actions_layout = QVBoxLayout(actions_group)
        self._actions_list = QListWidget(self)
        self._actions_list.setObjectName("actions_list")
        actions_layout.addWidget(self._actions_list)
        layout.addWidget(actions_group)

        self._refresh_button = QPushButton("Rafraîchir", self)
        self._refresh_button.setObjectName("refresh_button")
        self._refresh_button.clicked.connect(self._refresh)
        layout.addWidget(self._refresh_button)

    def _refresh(self) -> None:
        """Rafraîchit le contenu à partir du contrôleur."""
        status, reports, actions = self._controller.refresh()
        self._update_status(status)
        self._update_reports(reports)
        self._update_whisper_section()
        self._update_actions(actions)

    def _update_status(self, status: RuntimeStatus) -> None:
        """Met à jour le libellé de l'état global."""
        self._status_label.setText(f"État global : {status.name}")

    def _update_reports(self, reports: list[RuntimeReport]) -> None:
        """Remplit le tableau des rapports de diagnostic."""
        self._reports_table.setRowCount(len(reports))
        for row, report in enumerate(reports):
            self._reports_table.setItem(row, 0, QTableWidgetItem(report.provider_name))
            self._reports_table.setItem(row, 1, QTableWidgetItem(report.status.name))
            self._reports_table.setItem(row, 2, QTableWidgetItem(report.message))

    def _update_actions(self, actions: list[RuntimeAction]) -> None:
        """Remplit la liste des actions recommandées avec un emplacement bouton."""
        self._actions_list.clear()

        for index, action in enumerate(actions):
            item = QListWidgetItem(self._actions_list)
            widget = QWidget(self._actions_list)
            row_layout = QHBoxLayout(widget)
            row_layout.setContentsMargins(4, 2, 4, 2)

            label = QLabel(
                f"[{action.action_type.name}] {action.message}", widget
            )
            if action.description:
                label.setToolTip(action.description)
            row_layout.addWidget(label, stretch=1)

            button = QPushButton(self._action_button_text(action.action_type), widget)
            button.setObjectName(f"action_button_{index}")
            button.setEnabled(action.available)
            button.clicked.connect(partial(self._on_action_clicked, action))
            row_layout.addWidget(button)

            widget.setLayout(row_layout)
            item.setSizeHint(widget.sizeHint())
            self._actions_list.addItem(item)
            self._actions_list.setItemWidget(item, widget)

    def _action_button_text(self, action_type: RuntimeActionType) -> str:
        """Retourne le libellé du bouton selon le type d'action."""
        labels = {
            RuntimeActionType.INSTALL_PACKAGE: "Installer",
            RuntimeActionType.DOWNLOAD_MODEL: "Télécharger",
            RuntimeActionType.START_SERVER: "Démarrer",
            RuntimeActionType.CONFIGURE: "Configurer",
            RuntimeActionType.REPAIR: "Réparer",
            RuntimeActionType.RETRY: "Réessayer",
            RuntimeActionType.NONE: "—",
        }
        return labels.get(action_type, "Agir")

    def _on_action_clicked(self, action: RuntimeAction) -> None:
        """Gère le clic sur un bouton d'action.

        Pour les actions de téléchargement de modèle Whisper, l'installation
        est déclenchée directement. Les autres actions restent informatives.
        """
        if (
            action.action_type == RuntimeActionType.DOWNLOAD_MODEL
            and action.provider_name == "whisper"
        ):
            self._run_install(action.provider_name)
            return

        QMessageBox.information(
            self,
            "Action",
            f"L'action '{action.message}' sera implémentée prochainement.",
        )

    def _on_install_clicked(self) -> None:
        """Lance l'installation du modèle Whisper configuré."""
        self._run_install("whisper")

    def _run_install(self, provider_name: str) -> None:
        """Démarre le téléchargement du modèle pour le provider donné."""
        self._whisper_install_button.setEnabled(False)
        self._whisper_progress.setVisible(True)

        self._install_thread = _InstallThread(
            self._controller,
            provider_name,
            self,
        )
        self._install_thread.install_finished.connect(self._on_install_finished)
        self._install_thread.finished.connect(self._install_thread.deleteLater)
        self._install_thread.start()

    def _on_install_finished(self, report: RuntimeReport) -> None:
        """Gère la fin de l'installation et rafraîchit l'affichage."""
        self._whisper_progress.setVisible(False)

        if report.status == RuntimeStatus.HEALTHY:
            QMessageBox.information(
                self,
                "Installation terminée",
                report.message,
            )
        else:
            message = report.message
            error = report.details.get("error")
            if error:
                message += f"\n\nCause : {error}"
            QMessageBox.warning(
                self,
                "Échec de l'installation",
                message,
            )

        self._refresh()

    def _update_whisper_section(self) -> None:
        """Met à jour la section Whisper avec le diagnostic du provider."""
        report = self._controller.report_for("whisper")
        if report is None:
            self._whisper_provider_label.setText("Provider : inconnu")
            self._whisper_model_label.setText("Modèle :")
            self._whisper_status_label.setText("État :")
            self._whisper_path_label.setText("Emplacement :")
            self._whisper_info_label.setText("Information :")
            self._whisper_install_button.setEnabled(False)
            return

        details = report.details
        model_size = details.get("model_size", "—")
        model_path = details.get("model_path", "—")
        version = details.get("version", "")

        self._whisper_provider_label.setText(f"Provider : {report.provider_name}")
        self._whisper_model_label.setText(f"Modèle : {model_size}")
        self._whisper_status_label.setText(f"État : {report.status.name}")
        self._whisper_path_label.setText(f"Emplacement : {model_path}")

        info = report.message
        if version:
            info = f"v{version} — {info}"
        self._whisper_info_label.setText(f"Information : {info}")

        self._whisper_install_button.setEnabled(
            report.status != RuntimeStatus.HEALTHY
        )

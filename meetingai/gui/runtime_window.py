"""Fenêtre d'état du Runtime de MeetingAI."""

from __future__ import annotations

from functools import partial

import json
from collections.abc import Callable

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from meetingai.controllers.runtime_controller import RuntimeController
from meetingai.runtime.providers.ollama_runtime_provider import OllamaState
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


class _StartServerThread(QThread):
    """Thread de démarrage d'un serveur Runtime."""

    start_finished = Signal(RuntimeReport)

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
        """Démarre le serveur en arrière-plan."""
        report = self._controller.start_server(self._provider_name)
        self.start_finished.emit(report)


class _OperationThread(QThread):
    """Thread d'exécution d'une opération arbitraire du Runtime."""

    operation_finished = Signal(RuntimeReport)

    def __init__(
        self,
        operation: Callable[[], RuntimeReport],
        parent: QWidget | None = None,
    ) -> None:
        """Initialise le thread avec l'opération à exécuter."""
        super().__init__(parent)
        self._operation = operation

    def run(self) -> None:
        """Exécute l'opération en arrière-plan."""
        report = self._operation()
        self.operation_finished.emit(report)


class RuntimeWindow(QDialog):
    """Fenêtre affichant l'état du Runtime, les rapports et les actions proposées.

    La fenêtre s'appuie sur ``RuntimeController`` pour ne pas dupliquer la
    logique de diagnostic. Elle affiche des sections dédiées à Whisper et
    à Ollama, et permet d'installer les modèles ou de démarrer le serveur
    Ollama via le contrôleur.

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

    @staticmethod
    def _status_color(status: RuntimeStatus) -> str:
        """Retourne la couleur associée à un état du Runtime."""
        colors = {
            RuntimeStatus.HEALTHY: "#28a745",
            RuntimeStatus.DEGRADED: "#ffc107",
            RuntimeStatus.MISSING: "#dc3545",
            RuntimeStatus.ERROR: "#dc3545",
            RuntimeStatus.UNKNOWN: "#6c757d",
        }
        return colors.get(status, "#212529")

    def _style_status_label(self, label: QLabel, status: RuntimeStatus) -> None:
        """Met à jour un QLabel avec l'indicateur visuel de l'état."""
        color = self._status_color(status)
        label.setStyleSheet(
            f"QLabel {{ font-weight: bold; color: {color}; }}"
        )

    def _setup_ui(self) -> None:
        """Construit les sections de la fenêtre."""
        self.setMinimumSize(700, 500)
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("status_label")
        self._status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        content_layout.addWidget(self._status_label)

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
        content_layout.addWidget(reports_group)

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

        content_layout.addWidget(whisper_group)

        ollama_group = QGroupBox("Ollama", self)
        ollama_group.setObjectName("ollama_group")
        ollama_layout = QVBoxLayout(ollama_group)

        self._ollama_provider_label = QLabel("Provider :", self)
        self._ollama_provider_label.setObjectName("ollama_provider_label")
        ollama_layout.addWidget(self._ollama_provider_label)

        self._ollama_status_label = QLabel("État :", self)
        self._ollama_status_label.setObjectName("ollama_status_label")
        ollama_layout.addWidget(self._ollama_status_label)

        self._ollama_version_label = QLabel("Version :", self)
        self._ollama_version_label.setObjectName("ollama_version_label")
        ollama_layout.addWidget(self._ollama_version_label)

        self._ollama_server_label = QLabel("Serveur :", self)
        self._ollama_server_label.setObjectName("ollama_server_label")
        ollama_layout.addWidget(self._ollama_server_label)

        self._ollama_model_label = QLabel("Modèle configuré :", self)
        self._ollama_model_label.setObjectName("ollama_model_label")
        ollama_layout.addWidget(self._ollama_model_label)

        self._ollama_models_label = QLabel("Modèles installés :", self)
        self._ollama_models_label.setObjectName("ollama_models_label")
        self._ollama_models_label.setWordWrap(True)
        ollama_layout.addWidget(self._ollama_models_label)

        self._ollama_info_label = QLabel("Information :", self)
        self._ollama_info_label.setObjectName("ollama_info_label")
        self._ollama_info_label.setWordWrap(True)
        ollama_layout.addWidget(self._ollama_info_label)

        ollama_models_label = QLabel("Modèles installés :", self)
        ollama_layout.addWidget(ollama_models_label)

        self._ollama_models_list = QListWidget(self)
        self._ollama_models_list.setObjectName("ollama_models_list")
        ollama_layout.addWidget(self._ollama_models_list)

        self._ollama_model_input = QLineEdit(self)
        self._ollama_model_input.setObjectName("ollama_model_input")
        self._ollama_model_input.setPlaceholderText(
            "Nom du modèle à télécharger (ex. llama3.2)"
        )
        ollama_layout.addWidget(self._ollama_model_input)

        ollama_buttons_layout = QHBoxLayout()

        self._ollama_download_button = QPushButton("Télécharger", self)
        self._ollama_download_button.setObjectName("ollama_download_button")
        self._ollama_download_button.clicked.connect(self._on_ollama_download)
        ollama_buttons_layout.addWidget(self._ollama_download_button)

        self._ollama_select_button = QPushButton("Sélectionner", self)
        self._ollama_select_button.setObjectName("ollama_select_button")
        self._ollama_select_button.clicked.connect(self._on_ollama_select)
        ollama_buttons_layout.addWidget(self._ollama_select_button)

        self._ollama_remove_button = QPushButton("Supprimer", self)
        self._ollama_remove_button.setObjectName("ollama_remove_button")
        self._ollama_remove_button.clicked.connect(self._on_ollama_remove)
        ollama_buttons_layout.addWidget(self._ollama_remove_button)

        ollama_layout.addLayout(ollama_buttons_layout)

        self._ollama_progress = QProgressBar(self)
        self._ollama_progress.setObjectName("ollama_progress")
        self._ollama_progress.setRange(0, 0)
        self._ollama_progress.setTextVisible(False)
        self._ollama_progress.setVisible(False)
        ollama_layout.addWidget(self._ollama_progress)

        content_layout.addWidget(ollama_group)

        actions_group = QGroupBox("Actions recommandées", self)
        actions_layout = QVBoxLayout(actions_group)
        self._actions_list = QListWidget(self)
        self._actions_list.setObjectName("actions_list")
        actions_layout.addWidget(self._actions_list)
        content_layout.addWidget(actions_group)

        details_group = QGroupBox("Détails techniques", self)
        details_group.setObjectName("details_group")
        details_group.setCheckable(True)
        details_group.setChecked(False)
        details_layout = QVBoxLayout(details_group)
        self._details_edit = QTextEdit(self)
        self._details_edit.setObjectName("details_edit")
        self._details_edit.setReadOnly(True)
        self._details_edit.setVisible(False)
        details_layout.addWidget(self._details_edit)
        details_group.toggled.connect(self._details_edit.setVisible)
        content_layout.addWidget(details_group)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

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
        self._update_ollama_section()
        self._update_actions(actions)
        self._update_details(reports)

    def _update_status(self, status: RuntimeStatus) -> None:
        """Met à jour le libellé de l'état global avec un indicateur visuel."""
        self._status_label.setText(f"État global : {status.name}")
        self._style_status_label(self._status_label, status)

    def _update_reports(self, reports: list[RuntimeReport]) -> None:
        """Remplit le tableau des rapports de diagnostic."""
        self._reports_table.setRowCount(len(reports))
        self._reports_table.setWordWrap(True)
        self._reports_table.setTextElideMode(Qt.TextElideMode.ElideNone)

        header = self._reports_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        for row, report in enumerate(reports):
            name_item = QTableWidgetItem(report.provider_name)
            name_item.setToolTip(report.provider_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._reports_table.setItem(row, 0, name_item)

            status_item = QTableWidgetItem(report.status.name)
            status_item.setToolTip(report.status.name)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._reports_table.setItem(row, 1, status_item)

            message_item = QTableWidgetItem(report.message)
            message_item.setToolTip(report.message)
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._reports_table.setItem(row, 2, message_item)

            self._reports_table.resizeRowToContents(row)

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
            label.setWordWrap(True)
            if action.description:
                label.setToolTip(action.description)
            if action.available:
                label.setStyleSheet("font-weight: bold;")
            row_layout.addWidget(label, stretch=1)

            button = QPushButton(self._action_button_text(action.action_type), widget)
            button.setObjectName(f"action_button_{index}")
            button.setEnabled(action.available)
            button.clicked.connect(partial(self._on_action_clicked, action, button))
            row_layout.addWidget(button)

            widget.setLayout(row_layout)
            item.setSizeHint(widget.sizeHint())
            self._actions_list.addItem(item)
            self._actions_list.setItemWidget(item, widget)

    def _update_details(self, reports: list[RuntimeReport]) -> None:
        """Remplit la section Détails techniques avec les rapports."""
        details = {}
        for report in reports:
            details[report.provider_name] = {
                "status": report.status.name,
                "message": report.message,
                "details": report.details,
            }
        self._details_edit.setPlainText(json.dumps(details, indent=2, ensure_ascii=False))

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

    def _on_action_clicked(
        self,
        action: RuntimeAction,
        button: QPushButton | None = None,
    ) -> None:
        """Gère le clic sur un bouton d'action.

        Les actions supportées (téléchargement de modèle, démarrage de
        serveur) sont exécutées via le contrôleur dans un thread. Les autres
        actions affichent un message informatif.
        """
        if action.action_type == RuntimeActionType.DOWNLOAD_MODEL:
            if action.provider_name == "whisper":
                self._run_install(action.provider_name, self._whisper_progress, button)
            else:
                self._run_install(action.provider_name, self._ollama_progress, button)
            return

        if (
            action.action_type == RuntimeActionType.START_SERVER
            and action.provider_name == "ollama"
        ):
            self._run_start_server(action.provider_name, self._ollama_progress, button)
            return

        if (
            action.action_type == RuntimeActionType.INSTALL_PACKAGE
            and action.provider_name == "ollama"
        ):
            QMessageBox.information(
                self,
                "Installer Ollama",
                f"{action.description}\n\nVeuillez installer Ollama depuis "
                "https://ollama.com puis relancer l'application.",
            )
            return

        QMessageBox.information(
            self,
            "Action",
            f"L'action '{action.message}' sera implémentée prochainement.",
        )

    def _on_install_clicked(self) -> None:
        """Lance l'installation du modèle Whisper configuré."""
        self._run_install(
            "whisper",
            self._whisper_progress,
            self._whisper_install_button,
        )

    def _run_install(
        self,
        provider_name: str,
        progress: QProgressBar | None = None,
        button: QPushButton | None = None,
    ) -> None:
        """Démarre le téléchargement du modèle pour le provider donné."""
        if progress is None:
            progress = self._whisper_progress
        if button is not None:
            button.setEnabled(False)
        progress.setVisible(True)

        self._install_thread = _InstallThread(
            self._controller,
            provider_name,
            self,
        )
        self._install_thread.install_finished.connect(
            lambda report: self._on_install_finished(report, progress, button)
        )
        self._install_thread.finished.connect(self._install_thread.deleteLater)
        self._install_thread.start()

    def _on_install_finished(
        self,
        report: RuntimeReport,
        progress: QProgressBar,
        button: QPushButton | None,
    ) -> None:
        """Gère la fin de l'installation et rafraîchit l'affichage."""
        progress.setVisible(False)
        if button is not None:
            button.setEnabled(True)

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

    def _run_start_server(
        self,
        provider_name: str,
        progress: QProgressBar | None = None,
        button: QPushButton | None = None,
    ) -> None:
        """Démarre le serveur du provider donné."""
        if progress is None:
            progress = self._ollama_progress
        if button is not None:
            button.setEnabled(False)
        progress.setVisible(True)

        self._start_server_thread = _StartServerThread(
            self._controller,
            provider_name,
            self,
        )
        self._start_server_thread.start_finished.connect(
            lambda report: self._on_start_server_finished(report, progress, button)
        )
        self._start_server_thread.finished.connect(
            self._start_server_thread.deleteLater
        )
        self._start_server_thread.start()

    def _on_start_server_finished(
        self,
        report: RuntimeReport,
        progress: QProgressBar,
        button: QPushButton | None,
    ) -> None:
        """Gère la fin du démarrage du serveur et rafraîchit l'affichage."""
        progress.setVisible(False)
        if button is not None:
            button.setEnabled(True)

        if report.status == RuntimeStatus.HEALTHY:
            QMessageBox.information(
                self,
                "Démarrage terminé",
                report.message,
            )
        else:
            message = report.message
            error = report.details.get("error")
            if error:
                message += f"\n\nCause : {error}"
            QMessageBox.warning(
                self,
                "Échec du démarrage",
                message,
            )

        self._refresh()

    def _run_operation(
        self,
        operation: Callable[[], RuntimeReport],
        progress: QProgressBar,
        button: QPushButton | None,
        title: str,
        error_title: str,
    ) -> _OperationThread:
        """Exécute une opération longue dans un thread et affiche sa progression."""
        if button is not None:
            button.setEnabled(False)
        progress.setVisible(True)

        thread = _OperationThread(operation, self)
        thread.operation_finished.connect(
            lambda report: self._on_operation_finished(
                report, progress, button, title, error_title
            )
        )
        thread.finished.connect(thread.deleteLater)
        thread.start()
        return thread

    def _on_operation_finished(
        self,
        report: RuntimeReport,
        progress: QProgressBar,
        button: QPushButton | None,
        title: str,
        error_title: str,
    ) -> None:
        """Gère la fin d'une opération et rafraîchit l'affichage."""
        progress.setVisible(False)
        if button is not None:
            button.setEnabled(True)

        if report.status == RuntimeStatus.HEALTHY:
            QMessageBox.information(self, title, report.message)
        else:
            message = report.message
            error = report.details.get("error")
            if error:
                message += f"\n\nCause : {error}"
            QMessageBox.warning(self, error_title, message)

        self._refresh()

    def _on_ollama_download(self) -> None:
        """Lance le téléchargement du modèle saisi."""
        model_name = self._ollama_model_input.text().strip()
        if not model_name:
            QMessageBox.warning(
                self,
                "Modèle manquant",
                "Veuillez saisir un nom de modèle à télécharger.",
            )
            return

        self._run_operation(
            partial(self._controller.install_model, "ollama", model_name),
            self._ollama_progress,
            self._ollama_download_button,
            "Installation terminée",
            "Échec de l'installation",
        )

    def _on_ollama_select(self) -> None:
        """Sélectionne le modèle choisi dans la liste comme modèle actif."""
        item = self._ollama_models_list.currentItem()
        if item is None:
            QMessageBox.warning(
                self,
                "Aucun modèle",
                "Veuillez sélectionner un modèle dans la liste.",
            )
            return

        model_name = item.data(Qt.ItemDataRole.UserRole)
        self._run_operation(
            partial(self._controller.set_model, "ollama", model_name),
            self._ollama_progress,
            self._ollama_select_button,
            "Sélection terminée",
            "Échec de la sélection",
        )

    def _on_ollama_remove(self) -> None:
        """Supprime le modèle choisi dans la liste."""
        item = self._ollama_models_list.currentItem()
        if item is None:
            QMessageBox.warning(
                self,
                "Aucun modèle",
                "Veuillez sélectionner un modèle à supprimer.",
            )
            return

        model_name = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer le modèle '{model_name}' ?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._run_operation(
            partial(self._controller.remove_model, "ollama", model_name),
            self._ollama_progress,
            self._ollama_remove_button,
            "Suppression terminée",
            "Échec de la suppression",
        )

    def _update_ollama_section(self) -> None:
        """Met à jour la section Ollama avec le diagnostic du provider."""
        report = self._controller.report_for("ollama")
        if report is None:
            self._ollama_provider_label.setText("Provider : inconnu")
            self._ollama_status_label.setText("État :")
            self._ollama_version_label.setText("Version :")
            self._ollama_server_label.setText("Serveur :")
            self._ollama_model_label.setText("Modèle configuré :")
            self._ollama_models_label.setText("Modèles installés :")
            self._ollama_info_label.setText("Information :")
            self._ollama_models_list.clear()
            return

        details = report.details
        host = details.get("host", "—")
        version = details.get("version", "—")
        installed = details.get("installed_models", [])
        configured = details.get("model", "—")

        server_state = (
            "joignable"
            if version not in (None, "—", "unknown")
            else "arrêté ou inaccessible"
        )

        self._ollama_provider_label.setText(f"Provider : {report.provider_name}")
        self._ollama_provider_label.setToolTip(report.provider_name)
        self._ollama_provider_label.setStyleSheet("font-weight: bold;")
        self._ollama_status_label.setText(f"État : {report.status.name}")
        self._ollama_status_label.setToolTip(report.message)
        self._style_status_label(self._ollama_status_label, report.status)
        self._ollama_version_label.setText(f"Version : {version}")
        self._ollama_version_label.setStyleSheet("font-weight: bold;")
        self._ollama_version_label.setToolTip(str(version))
        self._ollama_server_label.setText(f"Serveur : {host} ({server_state})")
        self._ollama_server_label.setToolTip(str(host))
        self._ollama_model_label.setText(f"Modèle configuré : {configured}")
        self._ollama_model_label.setStyleSheet("font-weight: bold;")
        self._ollama_models_label.setText(
            f"Modèles installés : {', '.join(str(m) for m in installed) or 'aucun'}"
        )
        self._ollama_info_label.setText(f"Information : {report.message}")
        self._ollama_info_label.setToolTip(report.message)

        self._ollama_models_list.clear()
        for model in installed:
            item = QListWidgetItem(str(model))
            item.setData(Qt.ItemDataRole.UserRole, model)
            self._ollama_models_list.addItem(item)
            if str(model) == str(configured):
                item.setSelected(True)

        state = details.get("state", OllamaState.NOT_INSTALLED.value)
        server_ready = state in (
            OllamaState.SERVER_STARTED.value,
            OllamaState.MODEL_AVAILABLE.value,
        )
        self._ollama_download_button.setEnabled(server_ready)
        self._ollama_remove_button.setEnabled(server_ready)
        self._ollama_select_button.setEnabled(
            state != OllamaState.NOT_INSTALLED.value
        )

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
        self._whisper_provider_label.setToolTip(report.provider_name)
        self._whisper_provider_label.setStyleSheet("font-weight: bold;")
        self._whisper_model_label.setText(f"Modèle : {model_size}")
        self._whisper_model_label.setStyleSheet("font-weight: bold;")
        self._whisper_status_label.setText(f"État : {report.status.name}")
        self._whisper_status_label.setToolTip(report.message)
        self._style_status_label(self._whisper_status_label, report.status)
        self._whisper_path_label.setText(f"Emplacement : {model_path}")
        self._whisper_path_label.setToolTip(str(model_path))

        info = report.message
        if version:
            info = f"v{version} — {info}"
        self._whisper_info_label.setText(f"Information : {info}")
        self._whisper_info_label.setToolTip(info)

        self._whisper_install_button.setEnabled(
            report.status != RuntimeStatus.HEALTHY
        )

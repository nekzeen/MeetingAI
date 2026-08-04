"""Fenêtre d'état du Runtime de MeetingAI."""

from __future__ import annotations

from functools import partial

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
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


class RuntimeWindow(QDialog):
    """Fenêtre affichant l'état du Runtime, les rapports et les actions proposées.

    La fenêtre s'appuie sur ``RuntimeController`` pour ne pas dupliquer la
    logique de diagnostic. Les boutons d'action sont créés mais leur
    comportement final est volontairement limité : ils affichent un message
    informatif et préparent l'intégration future.

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

        Cette méthode est un emplacement pour le comportement final. Elle
        affiche actuellement un message informatif sans exécuter l'action.
        """
        QMessageBox.information(
            self,
            "Action",
            f"L'action '{action.message}' sera implémentée prochainement.",
        )

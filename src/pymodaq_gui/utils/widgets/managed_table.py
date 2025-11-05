"""
Standalone table widget with row management and validation.
Can be used independently or wrapped by TableParameter.
"""

from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QStyle,
)
from qtpy.QtCore import Signal


class ManagedTableWidget(QWidget):
    """Reusable table widget with row controls and delegate support.

    Shape is inferred from data if provided, otherwise uses columns/rows parameters.
    """

    valueChanged = Signal(list)  # Emits list of lists

    def __init__(
        self,
        data=None,
        columns=None,
        rows=None,
        enable_row_controls=True,
        max_display_rows=None,
        delegate=None,
        parent=None,
    ):
        super().__init__(parent)

        # Handle dict format: {column_name: [values]}
        if isinstance(data, dict):
            data, columns = self._dict_to_list(data, columns)

        # Infer shape from data if provided
        if data is not None and len(data) > 0:
            self._initial_data = data
            if columns is None:
                # Infer column count from first row
                num_cols = len(data[0]) if data else 3
                columns = [f"Column {i + 1}" for i in range(num_cols)]
            if rows is None:
                rows = len(data)
        else:
            self._initial_data = None
            if columns is None:
                columns = ["Column 1", "Column 2", "Column 3"]
            if rows is None:
                rows = 5

        self.columns = columns if isinstance(columns, list) else list(columns)
        self._delegate = delegate

        self._setup_ui(rows, enable_row_controls, max_display_rows or rows)

    def _setup_ui(self, rows, enable_row_controls, max_display_rows):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Table
        self.table = QTableWidget(rows, len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.setAlternatingRowColors(False)

        # Height constraint
        row_height = self.table.verticalHeader().defaultSectionSize()
        header_height = self.table.horizontalHeader().height()
        max_height = header_height + (row_height * max_display_rows) + 10
        self.table.setMaximumHeight(max_height)

        # Delegate
        if self._delegate:
            self.table.setItemDelegate(self._delegate)

        # Signals
        self.table.itemChanged.connect(self._on_item_changed)

        layout.addWidget(self.table)

        # Load initial data if provided
        if self._initial_data is not None:
            self.setValue(self._initial_data)

        # Row controls
        if enable_row_controls:
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 0, 0, 0)

            btn_add = QPushButton()
            btn_add.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            )
            btn_add.setToolTip("Add row")
            btn_add.setMaximumWidth(30)
            btn_add.clicked.connect(self.addRow)

            btn_remove = QPushButton()
            btn_remove.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
            )
            btn_remove.setToolTip("Remove selected row(s)")
            btn_remove.setMaximumWidth(30)
            btn_remove.clicked.connect(self.removeSelectedRows)

            btn_clear = QPushButton()
            btn_clear.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
            )
            btn_clear.setToolTip("Clear all")
            btn_clear.setMaximumWidth(30)
            btn_clear.clicked.connect(self.clearAll)

            button_layout.addWidget(btn_add)
            button_layout.addWidget(btn_remove)
            button_layout.addWidget(btn_clear)
            button_layout.addStretch()

            layout.addLayout(button_layout)

    def _on_item_changed(self):
        """Emit value changed signal."""
        self.valueChanged.emit(self.value())

    @staticmethod
    def _dict_to_list(data_dict, columns=None):
        """Convert dict format to list of lists.

        Args:
            data_dict: Dict with {column_name: [values]} format
            columns: Optional column order. If None, uses dict keys order.

        Returns:
            tuple: (list_of_lists, column_names)
        """
        if not data_dict:
            return [], []

        # Determine column order
        if columns is None:
            columns = list(data_dict.keys())

        # Verify all columns exist in dict
        for col in columns:
            if col not in data_dict:
                raise ValueError(f"Column '{col}' not found in data dict")

        # Get max length to handle uneven columns
        max_len = max(len(data_dict[col]) for col in columns)

        # Convert to list of lists
        list_data = []
        for i in range(max_len):
            row = []
            for col in columns:
                col_data = data_dict[col]
                row.append(str(col_data[i]) if i < len(col_data) else "")
            list_data.append(row)

        return list_data, columns

    @staticmethod
    def _list_to_dict(list_data, columns):
        """Convert list of lists to dict format.

        Args:
            list_data: List of lists
            columns: Column names

        Returns:
            dict: {column_name: [values]} format
        """
        result = {col: [] for col in columns}
        for row in list_data:
            for col_idx, col_name in enumerate(columns):
                if col_idx < len(row):
                    result[col_name].append(row[col_idx])
                else:
                    result[col_name].append("")
        return result

    def setValue(self, data):
        """Set table data from list of lists or dict."""
        if isinstance(data, dict):
            data, _ = self._dict_to_list(data, self.columns)

        if not data:
            return

        self.table.blockSignals(True)

        if len(data) != self.table.rowCount():
            self.table.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                if col_idx >= self.table.columnCount():
                    break
                item = QTableWidgetItem(str(cell_value))
                self.table.setItem(row_idx, col_idx, item)

        self.table.blockSignals(False)

    def value(self):
        """Get table data as list of lists."""
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def valueAsDict(self):
        """Get table data as dict with column names as keys."""
        return self._list_to_dict(self.value(), self.columns)

    def addRow(self, row_data=None):
        """Add a new row."""
        self.table.blockSignals(True)
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        if not row_data:
            row_data = [""] * self.table.columnCount()

        for col, value in enumerate(row_data):
            if col < self.table.columnCount():
                self.table.setItem(row_count, col, QTableWidgetItem(str(value)))

        self.table.blockSignals(False)
        self._on_item_changed()

    def removeSelectedRows(self):
        """Remove selected rows."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return

        self.table.blockSignals(True)
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
        self.table.blockSignals(False)
        self._on_item_changed()

    def removeRow(self, row_index):
        """Remove row by index."""
        if 0 <= row_index < self.table.rowCount():
            self.table.blockSignals(True)
            self.table.removeRow(row_index)
            self.table.blockSignals(False)
            self._on_item_changed()

    def clearAll(self):
        """Clear all cell data."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setText("")
                else:
                    self.table.setItem(row, col, QTableWidgetItem(""))
        self.table.blockSignals(False)
        self._on_item_changed()

    def setDelegate(self, delegate):
        """Set item delegate for validation."""
        self._delegate = delegate
        if delegate:
            self.table.setItemDelegate(delegate)

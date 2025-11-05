"""
Custom delegates for widget editing.
"""

from qtpy.QtWidgets import (
    QStyledItemDelegate,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QStyle,
)
from qtpy.QtCore import Qt, QEvent
from pymodaq_gui.utils.widgets.pattern_completer import PatternLineEdit
from pyqtgraph.widgets.SpinBox import SpinBox
from pymodaq_data import Q_

class NumericDelegate(QStyledItemDelegate):
    """Delegate for numeric input with spinbox."""

    def __init__(self, min_val=0, max_val=100, decimals=2):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals

    def createEditor(self, parent, option, index):
        if self.decimals > 0:
            editor = QDoubleSpinBox(parent)
            editor.setDecimals(self.decimals)
        else:
            editor = QSpinBox(parent)

        editor.setMinimum(self.min_val)
        editor.setMaximum(self.max_val)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        try:
            editor.setValue(float(value) if value else 0)
        except (ValueError, TypeError):
            editor.setValue(0)

    def setModelData(self, editor, model, index):
        editor.interpretText()
        value = editor.value()
        model.setData(index, str(value), Qt.EditRole)


class ComboBoxDelegate(QStyledItemDelegate):
    """Delegate for dropdown selection."""

    def __init__(self, items):
        super().__init__()
        self.items = items

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        # Auto-commit on selection change
        editor.currentIndexChanged.connect(lambda: self._commit_and_close(editor))
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        # Block signals during initial setup to avoid premature commit
        editor.blockSignals(True)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
        editor.blockSignals(False)
        # Show popup immediately
        editor.showPopup()

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

    def _commit_and_close(self, editor):
        """Commit and close editor when selection changes."""
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)


class ColumnSpecificDelegate(QStyledItemDelegate):
    """Delegate that applies different delegates to different columns."""

    def __init__(self, column_delegates):
        """
        Parameters
        ----------
        column_delegates : dict
            Dictionary mapping column indices to delegate instances.
            Example: {0: NumericDelegate(), 1: ComboBoxDelegate(['A', 'B'])}
        """
        super().__init__()
        self.column_delegates = column_delegates

    def createEditor(self, parent, option, index):
        col = index.column()
        if col in self.column_delegates:
            return self.column_delegates[col].createEditor(parent, option, index)
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        col = index.column()
        if col in self.column_delegates:
            self.column_delegates[col].setEditorData(editor, index)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        col = index.column()
        if col in self.column_delegates:
            self.column_delegates[col].setModelData(editor, model, index)
        else:
            super().setModelData(editor, model, index)


class ReadOnlyDelegate(QStyledItemDelegate):
    """Delegate that makes cells read-only."""

    def createEditor(self, parent, option, index):
        return None


class ColumnReadOnlyDelegate(QStyledItemDelegate):
    """Delegate that makes specific columns read-only."""

    def __init__(self, readonly_columns):
        """
        Parameters
        ----------
        readonly_columns : list
            List of column indices that should be read-only.
        """
        super().__init__()
        self.readonly_columns = set(readonly_columns)

    def createEditor(self, parent, option, index):
        if index.column() in self.readonly_columns:
            return None
        return super().createEditor(parent, option, index)


class PatternCompleterDelegate(QStyledItemDelegate):
    """
    Custom delegate for QTableWidget that uses PatternLineEdit with mixin.

    Usage:
        delegate = PatternCompleterDelegate(min_width=200, max_width=600)
        delegate.add_completer('@', ['USA', 'Canada', 'Mexico'])
        delegate.add_completer('#', ['Python', 'Java', 'C++'], case_sensitive=True)
        table.setItemDelegateForColumn(0, delegate)
    """

    def __init__(self, parent=None, **kwargs):
        """
        Initialize delegate with global configuration.

        Args:
            **kwargs: Global configuration options (same as init_pattern_completer)
        """
        super().__init__(parent)
        self.completer_configs = {}  # pattern -> config dict
        self.global_kwargs = kwargs

    def add_completer(self, pattern, completions, **kwargs):
        """
        Add a completer pattern for this delegate.

        Args:
            pattern: Trigger string (e.g., '@', '#')
            completions: List of completion strings
            **kwargs: Pattern-specific configuration (overrides global)
        """
        self.completer_configs[pattern] = {
            "completions": completions,
            "kwargs": kwargs,
        }

    def update_completions(self, pattern, completions):
        """Update the completion list for a specific pattern"""
        if pattern in self.completer_configs:
            self.completer_configs[pattern]["completions"] = completions

    def update_completer_config(self, pattern, **kwargs):
        """Update configuration for a specific pattern"""
        if pattern in self.completer_configs:
            self.completer_configs[pattern]["kwargs"].update(kwargs)

    def set_global_config(self, **kwargs):
        """Update global configuration"""
        self.global_kwargs.update(kwargs)

    def createEditor(self, parent, option, index):
        """Create a PatternLineEdit when editing starts"""
        try:
            editor = PatternLineEdit(parent, **self.global_kwargs)

            # Add all configured completers
            for pattern, config in self.completer_configs.items():
                editor.add_completer(
                    pattern, config["completions"], **config.get("kwargs", {})
                )

            return editor
        except Exception as e:
            print(f"Error creating editor: {e}")
            # Fallback to basic QLineEdit
            return QLineEdit(parent)

    def setEditorData(self, editor: PatternLineEdit, index):
        """Load data from model into editor"""
        try:
            if not editor or not index.isValid():
                return
            value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            if value is not None:
                editor.setText(str(value))
            else:
                editor.clear()
        except Exception as e:
            print(f"Error setting editor data: {e}")
            pass

    def setModelData(self, editor: PatternLineEdit, model, index):
        """Save data from editor back to model"""
        try:
            if not editor or not model or not index.isValid():
                return
            text = editor.text()
            model.setData(index, text, Qt.ItemDataRole.EditRole)
        except Exception as e:
            print(f"Error setting model data: {e}")
            pass

    def destroyEditor(self, editor: PatternLineEdit, index):
        """Clean up editor when done"""
        try:
            if editor and hasattr(editor, "cleanup_pattern_completer"):
                editor.cleanup_pattern_completer()
        except Exception as e:
            print(f"Error destroying editor: {e}")
            pass

        try:
            super().destroyEditor(editor, index)
        except Exception as e:
            print(f"Error in super destroyEditor: {e}")
            pass


class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, decimals=4, min=-1e6, max=1e6, units=None):
        self.decimals = decimals
        self.min = min
        self.max = max
        self.units = units
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        doubleSpinBox = SpinBox(parent)
        doubleSpinBox.setDecimals(self.decimals)
        doubleSpinBox.setMaximum(self.min)
        doubleSpinBox.setMaximum(self.max)
        if self.units is not None:
            doubleSpinBox.setSuffix(self.units)
        return doubleSpinBox

    def setEditorData(self, editor: SpinBox, index):
        data = index.data() if index.data() else 0
        editor.setValue(Q_(data).magnitude)
        # editor.setSuffix(Q_(index.data()).units)

    def setModelData(self, editor: SpinBox, model, index):
        model.setData(
            index,
            f"{editor.value()} {editor.opts['suffix']}"
            if self.units is not None
            else f"{editor.value()}",
            Qt.ItemDataRole.EditRole,
        )


class BooleanDelegate(QStyledItemDelegate):
    """
    TO implement custom widget editor for cells in a tableview
    """

    def __init__(self, check_symbol="True", cross_symbol="False", parent=None):
        super().__init__(parent)
        self.check_symbol = check_symbol
        self.cross_symbol = cross_symbol

    def createEditor(self, parent, option, index):
        boolean = QCheckBox(parent)
        return boolean

    def setEditorData(self, editor, index):
        value = str(index.data()).lower() in ("true", "1", "yes")
        editor.setChecked(value)

    def setModelData(self, editor, model, index):
        value = "True" if editor.isChecked() else "False"
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def displayText(self, value, locale):
        """Convert boolean to checkmark/cross."""
        is_true = str(value).lower() in ("true", "1", "yes")
        return self.check_symbol if is_true else self.cross_symbol


class YesNoDelegate(BooleanDelegate):
    """Boolean delegate showing 'Yes'/'No' (more readable than True/False)."""

    def __init__(self, parent=None):
        super().__init__(check_symbol="Yes", cross_symbol="No", parent=parent)


class CheckmarkDelegate(BooleanDelegate):
    """Boolean delegate showing ✓/✗ symbols (compact, visual)."""

    def __init__(self, parent=None):
        super().__init__(check_symbol="✓", cross_symbol="✗",parent=parent)



"""
Table parameter wrapping ManagedTableWidget.
"""

from pyqtgraph.parametertree.parameterTypes import WidgetParameterItem, SimpleParameter
from pymodaq_gui.utils.widgets.managed_table import ManagedTableWidget

class TableParameterItem(WidgetParameterItem):
    """Widget item wrapping ManagedTableWidget."""

    def __init__(self, param, depth):
        super().__init__(param, depth)
        self.hideWidget = False

    def makeWidget(self):
        """Create ManagedTableWidget."""
        opts = self.param.opts
        self.asSubItem = True

        # Get initial value/data
        initial_value = self.param.value()

        widget = ManagedTableWidget(
            data=initial_value,
            columns=opts.get("columns", None),  # Let widget infer if not provided
            rows=opts.get("rows", None),
            enable_row_controls=opts.get("enable_row_controls", True),
            max_display_rows=opts.get("max_display_rows", None),
            delegate=opts.get("delegate")() if "delegate" in opts else None,
        )
        # widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        widget.setStyleSheet("""
            ManagedTableWidget {
                background: transparent;
                border: none;
            }
        """)        
        # Connect signals
        widget.valueChanged.connect(self.widgetValueChanged)
        widget.sigChanged = widget.valueChanged

        self.widget = widget
        return widget

    def widgetValueChanged(self, data):
        """Handle widget value changes."""
        try:
            self.param.setValue(data)            
        except Exception as e:
            print(f"Error updating parameter: {e}")

    def setValue(self, val):
        """Set widget value."""
        self.widget.setValue(val)

    def value(self):
        """Get widget value."""
        return self.widget.value()

    def optsChanged(self, param, opts):
        """Handle option changes."""
        super().optsChanged(param, opts)

        if "value" in opts:
            self.widget.setValue(opts["value"])
            self.widget.table.resizeColumnsToContents()

        if "delegate" in opts:
            delegate = opts["delegate"]()
            self.widget.setDelegate(delegate)


class TableParameter(SimpleParameter):
    """Table parameter with row management and validation.

    Can be initialized with:
    - data: Infers shape from data
    - columns + rows: Empty table with specified shape
    - value: Legacy support (same as data)
    """

    itemClass = TableParameterItem

    def __init__(self, **opts):
        # Priority: data > value > columns/rows
        if "data" in opts:
            opts["value"] = opts.pop("data")

        if "value" not in opts:
            rows = opts.get("rows", 5)
            columns = opts.get("columns", ["Column 1", "Column 2", "Column 3"])
            opts["value"] = [[""] * len(columns) for _ in range(rows)]

        opts["expanded"] = True
        super().__init__(**opts)

    def valueIsDefault(self):
        return True

    def hasDefault(self):
        return False

    def setOpts(self, **opts):
        """Override to trigger optsChanged."""
        super().setOpts(**opts)
        for item in self.items:
            if hasattr(item, "optsChanged"):
                item.optsChanged(self, opts)

    def setValue(self, value, blockSignal=None):
        """Override to update widget."""
        super().setValue(value, blockSignal=blockSignal)
        for item in self.items:
            if hasattr(item, "setValue"):
                item.setValue(value)

    def addRow(self, row_data=None):
        """Add row programmatically."""
        current_value = self.value()
        if row_data is None:
            columns = self.opts.get("columns", ["Column 1", "Column 2", "Column 3"])
            row_data = [""] * len(columns)
        new_value = current_value + [row_data]
        self.setValue(new_value)

    def removeRow(self, row_index):
        """Remove row by index."""
        current_value = self.value()
        if 0 <= row_index < len(current_value):
            new_value = current_value[:row_index] + current_value[row_index + 1 :]
            self.setValue(new_value)

    def clearRows(self):
        """Clear all row data."""
        current_value = self.value()
        new_value = [[""] * len(row) for row in current_value]
        self.setValue(new_value)

    def valueAsDict(self):
        """Get value as dict with column names as keys.

        Returns:
            dict: {column_name: [column_values]}
        """
        columns = self.opts.get("columns", ["Column 1", "Column 2", "Column 3"])
        data = self.value()

        result = {col: [] for col in columns}
        for row in data:
            for col_idx, col_name in enumerate(columns):
                if col_idx < len(row):
                    result[col_name].append(row[col_idx])
                else:
                    result[col_name].append("")

        return result

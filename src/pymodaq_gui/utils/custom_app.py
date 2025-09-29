from abc import ABCMeta, abstractmethod
from typing import Union, TYPE_CHECKING, Dict

from qtpy.QtCore import QObject, QLocale, QEvent
from qtpy import QtCore, QtWidgets

from pyqtgraph.dockarea import DockArea

from pymodaq_gui.utils.dock import DockArea, Dock
from pymodaq_gui.managers.action_manager import ActionManager
from pymodaq_gui.managers.parameter_manager import ParameterManager


class CustomApp(QObject, ActionManager, ParameterManager):
    """Base Class to ease the implementation of User Interfaces

    Inherits the MixIns ActionManager and ParameterManager classes. You have to subclass some methods and make
    concrete implementation of a given number of methods:

    * setup_actions: mandatory, see :class:`pymodaq.utils.managers.action_manager.ActionManager`
    * value_changed: non mandatory, see :class:`pymodaq.utils.managers.parameter_manager.ParameterManager`
    * child_added: non mandatory, see :class:`pymodaq.utils.managers.parameter_manager.ParameterManager`
    * param_deleted: non mandatory, see :class:`pymodaq.utils.managers.parameter_manager.ParameterManager`
    * setup_docks: mandatory
    * setup_menu: non mandatory
    * connect_things: mandatory

    Parameters
    ----------
    parent: DockArea or QtWidget

    See Also
    --------
    :class:`pymodaq.utils.managers.action_manager.ActionManager`,
    :class:`pymodaq.utils.managers.parameter_manager.ParameterManager`,
    :class:`pymodaq.utils.managers.modules_manager.ModulesManager`,
    """

    log_signal = QtCore.Signal(str)
    params = []

    def __init__(self, parent: Union[DockArea, QtWidgets.QWidget]):
        QObject.__init__(self)
        ActionManager.__init__(self)
        ParameterManager.__init__(self)

        if not isinstance(parent, DockArea):
            if not isinstance(parent, QtWidgets.QWidget):
                raise Exception('no valid parent container, expected a DockArea or a least a QWidget')

        self.parent = parent
        if isinstance(parent, DockArea):
            self.dockarea: DockArea = parent
            self.mainwindow: QtWidgets.QMainWindow = parent.parent()
        else:
            self.dockarea: DockArea = None
            self.mainwindow: QtWidgets.QMainWindow = None

        self.docks: Dict[str, Dock] = dict([])
        self.statusbar = None
        self._toolbar = QtWidgets.QToolBar()
        self._menubar: QtWidgets.QMenuBar = None

        if self.mainwindow is not None:
            self.mainwindow.addToolBar(self._toolbar)
            self._menubar = self.mainwindow.menuBar()
            self.statusbar = self.mainwindow.statusBar()
            self.mainwindow.installEventFilter(self)
        self.set_toolbar(self._toolbar)

    def eventFilter(self, watched, event):
        """
           Handles `QEvent.Close` event sent to the main window by triggering `quit_fun`.

           Parameters
           ----------
           watched : QObject
               The object being watched for events.
           event : QEvent
               The event that occurred.
           Returns
           -------
           bool
               True if the event is handled and should not propagate further,
               otherwise False. Delegates to the parent implementation if applicable.
           """
        if watched is self.mainwindow and event.type() == QEvent.Close:
            self.quit_fun()
            try:
                return super().eventFilter(watched, event)
            finally:
                ...
        return False

    @abstractmethod
    def quit_fun(self):
        """
            A method executed when the window is cloded. It neeeds to be reimplemented in subclasses. It should take
            care of:
                - Stop any actions running in the background (acquisition, move, etc.)
                - Stop properly any thread
                - Release any held resource
                - Close the associated window
        """
        raise NotImplementedError

    def setup_ui(self):
        self.setup_docks()

        self.setup_actions()  # see ActionManager MixIn class

        try:
            self.setup_menu(self._menubar)
        except TypeError:
            self.setup_menu()  # for backcompatibility

        self.connect_things()

    def setup_docks(self):
        """Mandatory method to be subclassed to setup the docks layout

        Examples
        --------
        >>>self.docks['ADock'] = gutils.Dock('ADock name')
        >>>self.dockarea.addDock(self.docks['ADock'])
        >>>self.docks['AnotherDock'] = gutils.Dock('AnotherDock name')
        >>>self.dockarea.addDock(self.docks['AnotherDock'''], 'bottom', self.docks['ADock'])

        See Also
        --------
        pyqtgraph.dockarea.Dock
        """
        raise NotImplementedError

    def setup_menu(self, menubar: QtWidgets.QMenuBar = None):
        """Non mandatory method to be subclassed in order to create a menubar

        create menu for actions contained into the self._actions, for instance:

        Examples
        --------
        >>>file_menu = self._menubar.addMenu('File')
        >>>self.affect_to('load', file_menu)
        >>>self.affect_to('save', file_menu)

        >>>file_menu.addSeparator()
        >>>self.affect_to('quit', file_menu)

        See Also
        --------
        pymodaq.utils.managers.action_manager.ActionManager
        """
        pass

    def connect_things(self):
        """Connect actions and/or other widgets signal to methods"""
        raise NotImplementedError


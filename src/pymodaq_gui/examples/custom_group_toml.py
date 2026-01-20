from pathlib import Path
import datetime

import toml

from pymodaq_utils import config as config_mod
from pymodaq_gui.utils.widgets.tree_toml import TreeFromToml
from pymodaq_gui.parameter.pymodaq_ptypes import registerParameterType, GroupParameter

config_path = Path('./custom_toml_group.toml')


class CustomConfig(config_mod.BaseConfig):
    """Main class to deal with configuration values for this plugin"""
    config_template_path = config_path
    config_name = f"custom_settings"


child_template = [
    {'title': 'Do it?:', 'name': 'do_it', 'type': 'bool', 'value': True},
    {'title': 'Choose:', 'name': 'choice', 'type': 'list', 'value': 'ok',
     'limits': ['ok', 'nonok']},
]


class ScalableCustomGroup(GroupParameter):
    """
        |

        ================ =============
        **Attributes**    **Type**
        *opts*            dictionnary
        ================ =============

        See Also
        --------
        hardware.DAQ_Move_Stage_type
    """

    def __init__(self, **opts):
        opts['type'] = 'mycustomgroupparameter'
        opts['addText'] = "Add"
        opts['addList'] = [str(ind) for ind in range(10)]
        super().__init__(**opts)

    def addNew(self, typ):
        """
            Add a child.

            =============== ===========
            **Parameters**   **Type**
            *typ*            string
            =============== ===========
        """
        name_prefix = 'template'

        child_indexes = [int(par.name()[len(name_prefix) + 1:]) for par in self.children()[1:]]

        if child_indexes == []:
            newindex = 0
        else:
            newindex = max(child_indexes) + 1

        children = []
        for ind_child in range(int(typ)):
            newindex += ind_child
            children.append({'title': 'Template {:02.0f}'.format(newindex),
                             'name': f'{name_prefix}{newindex:02.0f}',
                             'type': 'group',
                             'removable': True, 'children': child_template})

        self.addChildren(children)


registerParameterType('mycustomgroupparameter', ScalableCustomGroup, override=True)


if __name__ == '__main__':
    from pymodaq_gui.utils.utils import mkQApp

    app = mkQApp('Dashboard')

    config = CustomConfig()

    tree_toml = TreeFromToml(config)
    tree_toml.show_dialog()

    app.exec()


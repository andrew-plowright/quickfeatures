# PyQGIS
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QMessageBox
from qgis.utils import showPluginHelp

# project
from quickfeatures.__about__ import __title__
from quickfeatures.gui.dlg_settings import MyPluginOptionsFactory
from quickfeatures.gui.plugin_widget import MyPluginWidget


class QuickFeatureCreatePlugin:

    def __init__(self, iface: QgisInterface):

        self.iface = iface

    def initGui(self):

        # settings page within the QGIS preferences menu
        self.options_factory = MyPluginOptionsFactory()
        self.iface.registerOptionsWidgetFactory(self.options_factory)

        # Action: Help button
        help_icon = QIcon(":/images/themes/default/mActionHelpContents.svg")
        self.action_help = QAction(help_icon, "Help", self.iface.mainWindow())
        self.action_help.triggered.connect(
            lambda: showPluginHelp(filename="resources/help/index")
        )
        self.iface.addPluginToMenu(__title__, self.action_help)

        # Action: Settings button
        wrench_icon = QIcon(":images/themes/default/console/iconSettingsConsole.svg")
        self.action_settings = QAction(wrench_icon, "Settings", self.iface.mainWindow())
        self.action_settings.triggered.connect(
            lambda: self.iface.showOptionsDialog(currentPage=f"{__title__} Options Page")
        )
        self.iface.addPluginToMenu(__title__, self.action_settings)

        # Load Dock Widget
        self.dockwidget = QDockWidget(__title__, self.iface.mainWindow())
        self.dockwidget.setWidget(MyPluginWidget(self.iface.mainWindow()))
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)


    def unload(self):

        # Clean up menu
        self.iface.removePluginMenu(__title__, self.action_help)
        self.iface.removePluginMenu(__title__, self.action_settings)

        # remove actions
        del self.action_settings
        del self.action_help

        # Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        # Clean up dock widget
        self.dockwidget.hide()
        self.iface.removeDockWidget(self.dockwidget)
        self.dockwidget.deleteLater()



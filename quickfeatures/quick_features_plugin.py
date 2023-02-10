# Project
from quickfeatures.__about__ import __title__
from quickfeatures.quick_features_settings import QuickFeaturesOptionsFactory
from quickfeatures.quick_features_widget import QuickFeaturesWidget

# qgis
from qgis.gui import QgisInterface
from qgis.utils import showPluginHelp

# PyQT
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget


class QuickFeaturesPlugin:

    def __init__(self, iface: QgisInterface):
        self.dock_widget = None
        self.action_settings = None
        self.action_help = None
        self.options_factory = None

        self.iface = iface

    def initGui(self):
        # settings page within the QGIS preferences menu
        self.options_factory = QuickFeaturesOptionsFactory()
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
            lambda: self.iface.showOptionsDialog(currentPage=f"{__title__}")
        )
        self.iface.addPluginToMenu(__title__, self.action_settings)

        # Load Dock Widget
        self.dock_widget = QDockWidget(__title__, self.iface.mainWindow())
        self.dock_widget.setWidget(QuickFeaturesWidget(self.iface.mainWindow()))
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def unload(self):
        # Clean up templates
        self.dock_widget.widget().clean_up()

        # Clean up menu
        self.iface.removePluginMenu(__title__, self.action_help)
        self.iface.removePluginMenu(__title__, self.action_settings)

        # remove actions
        del self.action_settings
        del self.action_help

        # Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        # Clean up dock widget
        self.dock_widget.hide()
        self.iface.removeDockWidget(self.dock_widget)
        self.dock_widget.deleteLater()

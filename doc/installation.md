# Installation

Two methods for installing this plugin.

### Method 1: Download latest release

Download the [latest release](https://github.com/andrew-plowright/quickfeatures/releases/latest).

In QGIS 3, click _Plugins_ in the menu bar, then _Manage and Install Plugins_. In the
left-hand panel, click _Install From Zip_ and
select the downloaded zip file to install the plugin.

![Manage and Install Plugins](qgis_install_plugin_window.png)

### Method 2: Clone from Github

Clone this repository to your local machine.

In QGIS 3, click _Settings_ in the menu bar, then _Options_. In the left-hand panel, click _System_, then
scroll down to the _Environment_ section.

Add a new environment variable named `QGIS_PLUGINPATH`. Set it to
_Append_ and set its value to the path to the cloned repository (the folder in which this README.md file is
located).

![Custom Environment Variables](qgis_custom_environment_variable.png)

Restart QGIS.

Then, click _Plugins_ in the menu bar, then _Manage and Install Plugins_. You should now find
"Quick Features" in the list of available plugins.
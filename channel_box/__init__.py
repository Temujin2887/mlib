__author__ = 'Danny Wynne'

import logging
import __main__

from ..core import qt
from ..core.qt import QtGui, QtCore
from . import channel_editor
from . import dock

log = logging.getLogger(__name__)

def install_channel_box():
	maya_win = qt.getMayaWindow()

	try:
		box_dock = __main__.__dict__[__name__+'_channel_box_dock']
		maya_win.removeDockWidget (box_dock)
	except KeyError:
		pass

	#box_dock = QtGui.QDockWidget(qt.getMayaWindow())
	#box_dock.setWindowTitle('Channel Box 2.0')
	#box_dock.setFeatures(QtGui.QDockWidget.DockWidgetClosable | QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)

	box_dock = dock.ChannelBoxDock(maya_win)
	cb_widget = channel_editor.ChannelBox()
	box_dock.setWidget(cb_widget)

	#maya_win.addDockWidget(QtCore.Qt.RightDockWidgetArea, box_dock)
	__main__.__dict__[__name__+'_channel_box_dock'] = box_dock

'''
import mlib.shelves
reload(mlib.shelves)
mlib.shelves.install_toolbar()
'''
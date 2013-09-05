__author__ = 'Danny Wynne'

from ..core import qt
from ..core.qt import QtGui, QtCore

class ChannelBoxDock(QtGui.QDockWidget):
	def __init__(self, parent = None):
		super(ChannelBoxDock, self).__init__(parent)
		self.setWindowTitle('Channel Box 2.0')
		self.setFeatures(QtGui.QDockWidget.DockWidgetClosable | QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable)
		parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)

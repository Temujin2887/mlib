__author__ = 'Danny Wynne'

from ..core import qt
from ..core.qt import QtGui, QtCore

baseclass = qt.loadUiFile("main")

class ChannelBox(baseclass):
	def __init__(self, parent = qt.getMayaWindow()):
		super(baseclass, self).__init__(parent)
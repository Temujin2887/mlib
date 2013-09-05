__author__ = 'Danny Wynne'

from ..core import qt
from ..core.qt import QtGui, QtCore
reload(qt)

baseclass = qt.loadUiFile("main")

class ChannelBox(baseclass):
	def __init__(self, parent = None):
		super(ChannelBox, self).__init__(parent)
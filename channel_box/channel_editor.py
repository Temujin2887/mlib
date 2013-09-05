__author__ = 'Danny Wynne'

from ..core import qt
from ..core.qt import QtGui, QtCore

baseclass = qt.loadUiFile("channel_editor")

class ChannelBox(baseclass):
	def __init__(self, parent = None):
		super(ChannelBox, self).__init__(parent)
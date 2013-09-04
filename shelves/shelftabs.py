__author__ = 'Nathan'


import logging

from ..core import qt
from ..core.qt import QtGui, QtCore



log = logging.getLogger(__name__)
QWIDGETSIZE_MAX = 16777215

class ShelfTabs(QtGui.QTabWidget):
	toolButtonStyleChanged = QtCore.Signal(QtCore.Qt.ToolButtonStyle)
	def __init__(self, parent=None):
		super(ShelfTabs, self).__init__(parent)

		trashBtn = buttons.TrashButton(self)
		self.setCornerWidget(trashBtn)
		self.setAcceptDrops(True)
		self.highlight = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)

		#self.setDocumentMode(True)
		self.setMovable(True)

		#Test code
		self.addTab(shelf.Shelf(self), 'Tab 1')
		self.addTab(shelf.Shelf(self), 'Tab 2')
		self.addTab(shelf.Shelf(self), 'Tab 3')
		#self.tabBar().hide()

	def addTab(self, tabWidget, *args):
		super(ShelfTabs, self).addTab(tabWidget, *args)
		self.toolButtonStyleChanged.connect(tabWidget.toolButtonStyleChanged.emit)

	def setOrientation(self, orientation):
		self.setMinimumSize(64, 64)
		for tabIndex in range(self.count()):
			tab = self.widget(tabIndex)
			tab.setOrientation(orientation)

	def setToolBarArea(self, area):
		if area == QtCore.Qt.TopToolBarArea or area == -1:
			self.setTabPosition(self.North)
		elif area == QtCore.Qt.BottomToolBarArea:
			self.setTabPosition(self.South)
		elif area == QtCore.Qt.LeftToolBarArea or area == -2:
			self.setTabPosition(self.West)
		elif area == QtCore.Qt.RightToolBarArea:
			self.setTabPosition(self.East)

		for tabIndex in range(self.count()):
			tab = self.widget(tabIndex)
			tab.setToolBarArea(area)

	def dragEnterEvent(self, event):
		tab = self.tabBar().tabAt(event.pos())
		if tab<0 or not self.tabBar().isVisible():
			event.ignore()
			self.highlight.hide()
		else:
			tabWidget = self.widget(tab)
			if tabWidget.widget()==event.source().parent():
				event.setDropAction(QtCore.Qt.MoveAction)
			else:
				event.setDropAction(QtCore.Qt.CopyAction)
			rect = self.tabBar().tabRect(tab)
			self.highlight.show()
			self.highlight.setGeometry(rect)
			event.accept(rect)

	def dragMoveEvent(self, event):
		tab = self.tabBar().tabAt(event.pos())
		if tab<0 or not self.tabBar().isVisible():
			event.ignore()
			self.highlight.hide()
		else:
			tabWidget = self.widget(tab)

			if tabWidget.widget()==event.source().parent():
				event.setDropAction(QtCore.Qt.MoveAction)
			else:
				event.setDropAction(QtCore.Qt.CopyAction)
			rect = self.tabBar().tabRect(tab)
			self.highlight.show()
			self.highlight.setGeometry(rect)
			event.accept(rect)

	def dragLeaveEvent(self, event):
		self.highlight.hide()

	def dropEvent(self, event):
		self.highlight.hide()

		tab = self.tabBar().tabAt(event.pos())
		tabWidget = self.widget(tab)

		#Make a fake drop event and pass it to the tab that was dropped onto
		tabDropEvent = QtGui.QDropEvent(
								QtCore.QPoint(99999, 99999),
				                event.dropAction(),
				                event.mimeData(),
				                event.mouseButtons(),
				                event.keyboardModifiers()
								)
		tabWidget.dropEvent(tabDropEvent)
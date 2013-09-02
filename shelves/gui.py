__author__ = 'Nathan'

import logging
import __main__

from functools import partial

from ..lib import qt
from ..lib.qt import QtGui, QtCore
from ..lib.widgets import flowlayout
from .widgets import buttons
from .widgets import shelf

reload(flowlayout)
reload(buttons)
reload(shelf)

import maya.cmds as cmds

log = logging.getLogger(__name__)
QWIDGETSIZE_MAX = 16777215


"""
Very placeholder!!

Goals:
	Support for left/right click menus in a more standard way (Using QToolButton popup modes and customContextMenuRequested)
	Support for per-button style sheets
	Support for a "highlight new" feature similar to the autodesk version, but with a per-tool version/date to define "new"
		Autodesk uses a version flag to highlight, which only works if your tools only change with maya updates.... lol
	Support for a "command library", buttons point to commands, no code in the button itself
		Resolves the issues that come when users copy buttons to custom shelves, and the code for the button on the primary shelf is updated.
		Allows for mixing and matching of commands, and re-using single commands
	Arbitrarily sized source icon images (bug still present after 3+ years)

Questions:
	User shelves versus "Shared" shelves?

"""

def install_toolbar():
	win = qt.getMayaWindow()
	try:
		bar = __main__.__dict__[__name__+'_toolbar']
		win.removeToolBar(bar)
	except KeyError:
		pass

	toolbar = ShelfBar(qt.getMayaWindow())
	win.addToolBar(toolbar)
	__main__.__dict__[__name__+'_toolbar'] = toolbar


class ShelfBar(QtGui.QToolBar):
	def __init__(self, parent=None):
		super(ShelfBar, self).__init__(parent)
		self.setWindowTitle('Maya Shelves 2.0')
		self.shelfTabs = ShelfTabs(self)
		#self.shelfOpts = ShelfOptions(self)
		self.toolButtonStyleChanged.connect(self.shelfTabs.toolButtonStyleChanged.emit)
		self.toolButtonStyleChanged.connect(self.updateLayout)

		self.orientationChanged.connect(partial(self.updateLayout, None))

		#self.addWidget(self.shelfOpts)
		self.addWidget(self.shelfTabs)
		self.setFloatable(False)

		self._last_state = (0, 0)
		self.setMinimumSize(QtCore.QSize(32, 32))

	def resizeEvent(self, event):
		QtGui.QToolBar.resizeEvent(self, event)
		orientation = self.orientation()
		if self.parent():
			area = self.parent().toolBarArea(self)
		else:
			area = 0

		if (area, orientation) != self._last_state:
			self._last_state = (area, orientation)
			self.updateLayout(self._last_state)

		self.update()
		self.updateGeometry()

	def sizeHint(self):
		return QtCore.QSize(64, 64)

	def updateLayout(self, state=None):
		if state is None:
			state = self._last_state
		area, orientation = state

		self.shelfTabs.setToolBarArea(area)
		self.shelfTabs.setOrientation(orientation)

		if self.isFloating():
			self.setFixedSize(64, 64)
		else:
			self.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)


		if orientation == QtCore.Qt.Vertical:
			if self.toolButtonStyle() == QtCore.Qt.ToolButtonTextBesideIcon:
				self.setMaximumWidth(90+32)
			else:
				self.setMaximumWidth(95)
			self.setMaximumHeight(QWIDGETSIZE_MAX)
		else:
			if self.toolButtonStyle() == QtCore.Qt.ToolButtonTextUnderIcon:
				self.setMaximumHeight(73+16)
			else:
				self.setMaximumHeight(73)
			self.setMaximumWidth(QWIDGETSIZE_MAX)

		self.updateGeometry()



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
		if orientation == QtCore.Qt.Vertical:
			pass

		for tabIndex in range(self.count()):
			tab = self.widget(tabIndex)
			tab.setOrientation(orientation)

	def setToolBarArea(self, area):
		if area == QtCore.Qt.TopToolBarArea:
			self.setTabPosition(self.North)
		elif area == QtCore.Qt.BottomToolBarArea:
			self.setTabPosition(self.South)
		elif area == QtCore.Qt.LeftToolBarArea:
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




'''
import mutil.shelves.gui
reload(mutil.shelves.gui)
mutil.shelves.gui.install_toolbar()
'''
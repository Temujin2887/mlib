__author__ = 'Nathan'

import logging
import __main__

from functools import partial

from ..core import qt
from ..core.qt import QtGui, QtCore
from ..core.widgets import flowlayout
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
		self.shelfOpts = ShelfOptions(self)
		self.toolButtonStyleChanged.connect(self.shelfTabs.toolButtonStyleChanged.emit)
		self.toolButtonStyleChanged.connect(self.updateLayout)

		self.orientationChanged.connect(partial(self.checkLayoutUpdate))

		self.shelfOpts.optionsMenu.aboutToShow.connect(self.buildOptionsMenu)
		self.shelfOpts.switchTabsMenu.aboutToShow.connect(self.buildSwitcherMenu)


		self.addWidget(self.shelfOpts)
		self.addWidget(self.shelfTabs)
		self.setFloatable(False)

		self._last_state = (0, 0)

		self.radioPixmaps = self.generateRadioPixmaps()

	def generateRadioPixmaps(self):
		"""
		Generate a set of circular "radio button" icons that look just like Mayas
		"""
		icons = {}
		for state in [QtGui.QStyle.State_On, QtGui.QStyle.State_Off]:
			pix = QtGui.QPixmap(16, 16)
			pix.fill(QtCore.Qt.transparent)

			painter = QtGui.QPainter(pix)

			opt = QtGui.QStyleOptionButton()
			opt.initFrom(self)
			opt.rect = pix.rect()
			opt.state = QtGui.QStyle.State_Enabled|state

			self.style().drawControl(QtGui.QStyle.CE_RadioButton, opt, painter)
			painter.end()

			icons[state] = QtGui.QIcon(pix)

		return icons

	def buildSwitcherMenu(self):
		"""
		Generate the tab switcher menu
		"""
		menu = self.sender()
		menu.clear()

		for tabIndex in range(self.shelfTabs.count()):
			label = self.shelfTabs.tabText(tabIndex)
			action = menu.addAction(label, partial(self.shelfTabs.setCurrentIndex, tabIndex))
			assert isinstance(action, QtGui.QAction)
			if tabIndex == self.shelfTabs.currentIndex():
				action.setIcon(self.radioPixmaps[QtGui.QStyle.State_On])
			else:
				action.setIcon(self.radioPixmaps[QtGui.QStyle.State_Off])

	def buildOptionsMenu(self):
		menu = self.sender()
		menu.clear()
		assert isinstance(menu, QtGui.QMenu)

		tabsVisible = self.shelfTabs.tabBar().isVisible()
		action = menu.addAction('Shelf Tabs', partial(self.shelfTabs.tabBar().setVisible, not tabsVisible))
		action.setCheckable(True)
		action.setChecked(tabsVisible)

		menu.addSeparator()
		menu.addAction('Shelf Editor...')
		menu.addSeparator()
		menu.addAction('New Shelf')
		menu.addAction('Delete Shelf')
		menu.addSeparator()
		menu.addAction('Load Shelf...')
		menu.addSeparator()
		menu.addAction('Save All Shelves')

	def resizeEvent(self, event):
		QtGui.QToolBar.resizeEvent(self, event)
		#self.checkLayoutUpdate()

	def event(self, event):
		if event.type() == QtCore.QEvent.Show:
			self.checkLayoutUpdate()
		return QtGui.QToolBar.event(self, event)


	def checkLayoutUpdate(self, orientation=None):
		orientation = self.orientation()
		if self.parent():
			area = self.parent().toolBarArea(self)
		else:
			area = QtCore.Qt.NoToolBarArea
		floating = self.isFloating()
		if floating:
			area = QtCore.Qt.NoToolBarArea

		if (area, orientation) != self._last_state:
			self._last_state = (area, orientation)
			self.updateLayout(self._last_state)


	def updateLayout(self, state=None):
		if state is None:
			state = self._last_state
		area, orientation = state

		self.shelfTabs.setToolBarArea(area or -orientation)
		self.shelfTabs.setOrientation(orientation)
		self.shelfOpts.setOrientation(orientation)

		print 'Update Layout:', state

		self.setMinimumSize(QtCore.QSize(64, 64))

		if orientation == QtCore.Qt.Vertical:
			if self.toolButtonStyle() == QtCore.Qt.ToolButtonTextBesideIcon:
				self.setMaximumWidth(90+32)
			else:
				self.setMaximumWidth(95)
			self.setMinimumHeight(256)
			self.setMaximumHeight(QWIDGETSIZE_MAX)
		else:
			if self.toolButtonStyle() == QtCore.Qt.ToolButtonTextUnderIcon:
				self.setMaximumHeight(73+16)
			else:
				self.setMaximumHeight(73)
			self.setMinimumWidth(256)
			self.setMaximumWidth(QWIDGETSIZE_MAX)

		self.layout().invalidate()
		self.updateGeometry()
		self.update()


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


class ShelfOptions(QtGui.QFrame):
	switchMenuAboutToShow = QtCore.Signal()
	def __init__(self, parent=None):
		super(ShelfOptions, self).__init__(parent)

		self.setFrameShape(self.Panel)
		self.setFrameShadow(self.Sunken)



		#Create buttons and style them
		self.switchTabBtn = QtGui.QToolButton(self)
		self.switchTabBtn.setAutoRaise(True)
		self.switchTabBtn.setPopupMode(QtGui.QToolButton.InstantPopup)
		self.switchTabBtn.setIconSize(QtCore.QSize(19, 10))
		self.switchTabBtn.setFixedSize(20, 15)
		self.switchTabBtn.setStyleSheet('QToolButton::menu-indicator { image: none; } QToolButton{padding: 0px 0px 0px 0px; margins: 0px 0px 0px 0px; border: none;}')
		self.switchTabBtn.setIcon(buttons.makeIcon(':/shelfTab.png'))
		self.switchTabBtn.setToolTip('Switch Tabs Quickly')

		self.optionsBtn = QtGui.QToolButton(self)
		self.optionsBtn.setAutoRaise(True)
		self.optionsBtn.setPopupMode(QtGui.QToolButton.InstantPopup)
		self.optionsBtn.setIconSize(QtCore.QSize(13, 8))
		self.optionsBtn.setFixedSize(20, 15)
		self.optionsBtn.setStyleSheet('QToolButton::menu-indicator { image: none; } QToolButton{padding: 0px 0px 0px 0px; margins: 0px 0px 0px 0px; border: none;}')
		self.optionsBtn.setIcon(buttons.makeIcon(':/arrowDown.png'))
		self.optionsBtn.setToolTip('Shelf modification options')

		self.switchTabsMenu = QtGui.QMenu(self.switchTabBtn)
		self.switchTabsMenu.setObjectName('tabSwitchMenu')
		self.optionsMenu = QtGui.QMenu(self.optionsBtn)
		self.optionsMenu.setObjectName('tabOptionsMenu')

		self.optionsBtn.setMenu(self.optionsMenu)
		self.switchTabBtn.setMenu(self.switchTabsMenu)

		self.separator = QtGui.QFrame(self)
		self.spacer = QtGui.QSpacerItem(128, 128, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)


		self.boxlayout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom, self)
		self.setLayout(self.boxlayout)
		self.layout().setContentsMargins(1, 1, 1, 1)
		self.layout().setSpacing(0)
		self.layout().addWidget(self.switchTabBtn)
		self.layout().addWidget(self.separator)
		self.layout().addWidget(self.optionsBtn)


	def setOrientation(self, orientation):
		for i in range(self.boxlayout.count()):
			if self.boxlayout.itemAt(i) is self.spacer:
				self.boxlayout.takeAt(i)
				break


		if orientation == QtCore.Qt.Vertical:
			self.boxlayout.addItem(self.spacer)
			self.setFixedSize(QWIDGETSIZE_MAX, 24)
			self.boxlayout.setDirection(QtGui.QBoxLayout.LeftToRight)
			self.separator.setFrameStyle(QtGui.QFrame.VLine)
		else:
			self.boxlayout.insertItem(0, self.spacer)
			self.setFixedSize(24, QWIDGETSIZE_MAX)
			self.boxlayout.setDirection(QtGui.QBoxLayout.TopToBottom)
			self.separator.setFrameStyle(QtGui.QFrame.HLine)

		#self.layout().invalidate()
		#self.updateGeometry()



'''
import mutil.shelves.gui
reload(mutil.shelves.gui)
mutil.shelves.gui.install_toolbar()
'''
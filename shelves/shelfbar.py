__author__ = 'Nathan'

from functools import partial

from ..core import qt
from ..core.qt import QtGui, QtCore

from . import util
from . import shelftabs

reload(util)
reload(shelftabs)

QWIDGETSIZE_MAX = 16777215

class ShelfBar(QtGui.QToolBar):
	"""
	Shelf bar class, handles embedding and orienting in a MainWindow
	"""
	areaChanged = QtCore.Signal(QtCore.Qt.ToolBarArea)
	def __init__(self, parent=None):
		super(ShelfBar, self).__init__(parent)
		self.setWindowTitle('Maya Shelves 2.0')
		self.setFloatable(False)
		self.__last_area = QtCore.Qt.NoToolBarArea
		self.areaChanged.emit(QtCore.Qt.NoToolBarArea)

		self.shelfTabs = shelftabs.ShelfTabs(self)
		self.shelfOpts = ShelfOptions(self)

		self.addWidget(self.shelfOpts)
		self.addWidget(self.shelfTabs)

		#Signals
		self.orientationChanged.connect(self.updateLayout)
		self.areaChanged.connect(self.updateLayout)
		self.toolButtonStyleChanged.connect(self.updateLayout)

		self.orientationChanged.connect(self.shelfOpts.setOrientation)
		self.orientationChanged.connect(self.shelfTabs.setOrientation)
		self.areaChanged.connect(self.shelfTabs.setToolBarArea)

	def tabWidget(self):
		return self.shelfTabs

	def event(self, event):
		#Check for a Show event, since that occurs when the toolbar changes state (Floating<=>Docked)
		if event.type() == QtCore.QEvent.Show:
			area = self.getToolbarArea()
			if area != self.__last_area:
				self.__last_area = area
				self.areaChanged.emit(area)
		return QtGui.QToolBar.event(self, event)

	def getToolbarArea(self):
		"""
		Fetch this toolbars current toolbar area

		:return: Toolbar area
		:rtype: QtCore.Qt.ToolBarArea
		"""
		if self.parent() and not self.isFloating():
			area = self.parent().toolBarArea(self)
		else:
			area = QtCore.Qt.NoToolBarArea
		return area

	def updateLayout(self):
		"""
		Update the layout of the toolbar
		"""
		orientation = self.orientation()
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
				self.setMaximumHeight(74)
			self.setMinimumWidth(256)
			self.setMaximumWidth(QWIDGETSIZE_MAX)

		#Invalidate everything
		self.layout().invalidate()
		self.updateGeometry()
		self.update()


class ShelfOptions(QtGui.QFrame):
	"""
	Custom widget that handles the layout and widgets for the toolbar "options" section
	"""
	def __init__(self, shelf):
		assert isinstance(shelf, ShelfBar)
		super(ShelfOptions, self).__init__(shelf)

		self.setFrameShape(self.Panel)
		self.setFrameShadow(self.Sunken)

		#Create buttons and style them
		self.switchTabBtn = QtGui.QToolButton(self)
		self.switchTabBtn.setAutoRaise(True)
		self.switchTabBtn.setPopupMode(QtGui.QToolButton.InstantPopup)
		self.switchTabBtn.setIconSize(QtCore.QSize(19, 10))
		self.switchTabBtn.setFixedSize(20, 15)
		self.switchTabBtn.setStyleSheet('QToolButton::menu-indicator { image: none; } QToolButton{padding: 0px 0px 0px 0px; margins: 0px 0px 0px 0px; border: none;}')
		self.switchTabBtn.setIcon(util.makeIcon(':/shelfTab.png'))
		self.switchTabBtn.setToolTip('Switch Tabs Quickly')

		self.optionsBtn = QtGui.QToolButton(self)
		self.optionsBtn.setAutoRaise(True)
		self.optionsBtn.setPopupMode(QtGui.QToolButton.InstantPopup)
		self.optionsBtn.setIconSize(QtCore.QSize(13, 8))
		self.optionsBtn.setFixedSize(20, 15)
		self.optionsBtn.setStyleSheet('QToolButton::menu-indicator { image: none; } QToolButton{padding: 0px 0px 0px 0px; margins: 0px 0px 0px 0px; border: none;}')
		self.optionsBtn.setIcon(util.makeIcon(':/arrowDown.png'))
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

		self.setOrientation(QtCore.Qt.Horizontal)

		self.radioPixmaps = self.generateRadioPixmaps()

		self.switchTabsMenu.aboutToShow.connect(self.buildSwitcherMenu)

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

		tabWidget = self.parent().tabWidget()

		for tabIndex in range(tabWidget.count()):
			label = tabWidget.tabText(tabIndex)
			action = menu.addAction(label, partial(tabWidget.setCurrentIndex, tabIndex))
			assert isinstance(action, QtGui.QAction)
			if tabIndex == tabWidget.currentIndex():
				action.setIcon(self.radioPixmaps[QtGui.QStyle.State_On])
			else:
				action.setIcon(self.radioPixmaps[QtGui.QStyle.State_Off])

	def buildOptionsMenu(self):
		menu = self.sender()
		menu.clear()
		assert isinstance(menu, QtGui.QMenu)

		tabWidget = self.parent().tabWidget()
		tabBar = tabWidget.tabBar()
		tabsVisible = tabBar.isVisible()

		action = menu.addAction('Shelf Tabs', partial(tabBar.setVisible, not tabsVisible))
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

	def setOrientation(self, orientation):
		"""
		Update the options orientation to match the current layout direction

		:param orientation: New orientation
		:type orientation: QtCore.Qt.Orientation
		"""
		#Remove the spacer, since we have to move change it from Begining<=>End
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

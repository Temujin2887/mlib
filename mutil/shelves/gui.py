__author__ = 'Nathan'

import __main__
from ..lib import qt
from ..lib.qt import QtGui, QtCore
from ..lib.widgets.flowlayout import FlowLayout

QWIDGETSIZE_MAX = 16777215


"""
Very placeholder!!

Goals:
	Support for left/right click menus in a more standard way (Using QToolButton, rather than a hacked QLabel like default shelves)
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

	toolbar = MayaShelfBar(qt.getMayaWindow())
	win.addToolBar(toolbar)
	__main__.__dict__[__name__+'_toolbar'] = toolbar


class MayaShelfBar(QtGui.QToolBar):
	def __init__(self, parent=None):
		super(MayaShelfBar, self).__init__(parent)
		self.setWindowTitle('Maya Shelves 2.0')
		self.shelfTabs = MayaShelves(self)
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
			self.updateLayout(area, orientation)
			self._last_state = (area, orientation)

	def updateLayout(self, area, orientation):
		self.shelfTabs.setToolBarArea(area)
		self.shelfTabs.setOrientation(orientation)

		if orientation == QtCore.Qt.Vertical:
			self.setMaximumWidth(90)
			self.setMaximumHeight(QWIDGETSIZE_MAX)
		else:
			self.setMaximumWidth(QWIDGETSIZE_MAX)
			self.setMaximumHeight(73)



class MayaShelf(QtGui.QScrollArea):
	def __init__(self, parent=None):
		super(MayaShelf, self).__init__(parent)
		self.setFrameStyle(QtGui.QFrame.NoFrame)
		self.verticalScrollBar().setSingleStep(32)
		self.verticalScrollBar().setPageStep(32)
		self.horizontalScrollBar().setSingleStep(32)
		self.horizontalScrollBar().setPageStep(32)

		self.setStyleSheet('QScrollBar:vertical { background: rgb(80, 80, 80); }')

		self.setObjectName('mayaShelfContentsScroll')
		self.setWidgetResizable(True)

		contents = QtGui.QWidget(self)
		contents.setObjectName('mayaShelfContents')
		self.setWidget(contents)

		self.shelfLayout = FlowLayout(contents)
		self.shelfLayout.setObjectName('shelfLayout')
		contents.setContentsMargins(2, 3, 0, 0)
		contents.setLayout(self.shelfLayout)
		self.shelfLayout.setSpacing(0)

		#Test code
		import random
		for i in range(random.randint(5, 25)):
			btn = ShelfButton()
			btn.setIconSize(QtCore.QSize(32, 32))
			btn.setMinimumSize(QtCore.QSize(32, 32))
			btn.setIcon(makeIcon(':/sphere.png'))
			btn.setText('test %s'%i)
			self.shelfLayout.addWidget(btn)


	def load(self, path):
		pass

	def save(self, path):
		pass

class MayaShelves(QtGui.QTabWidget):
	def __init__(self, parent=None):
		super(MayaShelves, self).__init__(parent)

		#Test code
		self.addTab(MayaShelf(self), 'Tab 1')
		self.addTab(MayaShelf(self), 'Tab 2')
		self.addTab(MayaShelf(self), 'Tab 3')

	def setOrientation(self, orientation):
		if orientation == QtCore.Qt.Vertical:
			pass
		pass

	def setToolBarArea(self, area):
		if area == QtCore.Qt.TopToolBarArea:
			self.setTabPosition(self.North)
		elif area == QtCore.Qt.BottomToolBarArea:
			self.setTabPosition(self.South)
		elif area == QtCore.Qt.LeftToolBarArea:
			self.setTabPosition(self.West)
		elif area == QtCore.Qt.RightToolBarArea:
			self.setTabPosition(self.East)


class ShelfButton(QtGui.QToolButton):
	def __init__(self, parent=None):
		super(ShelfButton, self).__init__(parent)
		self.setAutoRaise(True)
		#self.setStyleSheet('QToolButton{margin: 0px 0px 0px 0px; border:none;}')

def makeIcon(path):
	pixmap_normal = QtGui.QPixmap(path)
	pixmap_over = pixmap_normal.copy()
	painter = QtGui.QPainter(pixmap_over)

	alpha = QtGui.QPixmap(pixmap_over.size())
	alpha.fill(QtGui.QColor(100, 100, 100))
	pixmap_dode = pixmap_normal.copy()
	pixmap_dode.setAlphaChannel(alpha)

	painter.setCompositionMode(painter.CompositionMode_ColorDodge)
	painter.drawPixmap(0, 0, pixmap_dode)

	painter.end()
	icon = QtGui.QIcon()
	icon.addPixmap(pixmap_normal, icon.Normal, icon.On)
	icon.addPixmap(pixmap_over, icon.Active, icon.On)
	return icon

'''
import mutil.shelves.gui
reload(mutil.shelves.gui)
mutil.shelves.gui.install_toolbar()
'''
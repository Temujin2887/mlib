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
		self.tabs = MayaShelves(self)
		self.addWidget(self.tabs)
		self.setFloatable(False)

		self._last_state = (0, 0)

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
		if area == QtCore.Qt.TopToolBarArea:
			self.tabs.setTabPosition(self.tabs.North)
		elif area == QtCore.Qt.BottomToolBarArea:
			self.tabs.setTabPosition(self.tabs.South)
		elif area == QtCore.Qt.LeftToolBarArea:
			self.tabs.setTabPosition(self.tabs.West)
		elif area == QtCore.Qt.RightToolBarArea:
			self.tabs.setTabPosition(self.tabs.East)

		if orientation == QtCore.Qt.Vertical:
			self.setMaximumWidth(73)
			self.setMaximumHeight(QWIDGETSIZE_MAX)
		else:
			self.setMaximumWidth(QWIDGETSIZE_MAX)
			self.setMaximumHeight(73)

class MayaShelves(QtGui.QTabWidget):
	def __init__(self, parent=None):
		super(MayaShelves, self).__init__(parent)

		#Scroll Area flowLayout way
		scrollArea = QtGui.QScrollArea(self)
		scrollArea.setWidgetResizable(True)
		contents = QtGui.QWidget(scrollArea)
		scrollArea.setWidget(contents)
		self.addTab(scrollArea, 'TAB 1')
		contents.show()


		lyt = FlowLayout(contents)
		contents.setContentsMargins(0, 0, 0, 0)
		contents.setLayout(lyt)

		lyt.addWidget(self.createToolButton())
		lyt.addWidget(self.createToolButton())
		lyt.addWidget(self.createToolButton())
		lyt.addWidget(self.createToolButton())

	def createToolButton(self):
		btn = QtGui.QToolButton()
		btn.setStyleSheet('QToolButton{margin: 0px 0px 0px 0px; border:none;}')
		btn.setText('TEST')
		#btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		btn.setAutoRaise(True)
		btn.setMouseTracking(True)
		btn.setIcon(self.makeIcon(':/sphere.png'))
		btn.setIconSize(QtCore.QSize(32, 32))
		btn.setMenu(QtGui.QMenu(btn))
		btn.menu().addAction('TEST0')
		btn.menu().addAction('TEST1')
		return btn

	def makeIcon(self, path):
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


class ShelfButton(QtGui.QToolButton):
	pass

'''
import mutil.shelves.gui
reload(mutil.shelves.gui)
mutil.shelves.gui.install_toolbar()
'''
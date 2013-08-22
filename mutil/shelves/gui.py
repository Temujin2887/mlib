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
		self.orientationChanged.connect(self.updateSizing)
		self.updateSizing()

	def updateSizing(self):
		if self.orientation() == QtCore.Qt.Vertical:
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
		contents.setContentsMargins(2, 5, 2, 2)
		contents.setLayout(lyt)

		lyt.addWidget(self.createToolButton())
		lyt.addWidget(self.createToolButton())
		lyt.addWidget(self.createToolButton())
		lyt.addWidget(self.createToolButton())

	def createToolButton(self):
		btn = QtGui.QToolButton()
		btn.setStyleSheet('QToolButton{margin: 0px 0px 0px 0px; border:none;}')
		btn.setText('TEST')
		btn.setAutoRaise(True)
		btn.setMouseTracking(True)
		btn.setIcon(self.makeIcon(':/sphere.png'))
		btn.setIconSize(QtCore.QSize(32, 32))
		btn.setFixedSize(32, 32)
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
__author__ = 'Nathan'

import __main__
from ..lib import qt
from ..lib.qt import QtGui, QtCore
from ..lib.widgets import flowlayout
reload(flowlayout)


import maya.cmds as cmds

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

	toolbar = ShelfBar(qt.getMayaWindow())
	win.addToolBar(toolbar)
	__main__.__dict__[__name__+'_toolbar'] = toolbar


class ShelfBar(QtGui.QToolBar):
	def __init__(self, parent=None):
		super(ShelfBar, self).__init__(parent)
		self.setWindowTitle('Maya Shelves 2.0')
		self.shelfTabs = ShelfTabs(self)
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


class ShelfTabs(QtGui.QTabWidget):
	def __init__(self, parent=None):
		super(ShelfTabs, self).__init__(parent)

		trashBtn = TrashButton(self)
		self.setCornerWidget(trashBtn)

		#Test code
		self.addTab(Shelf(self), 'Tab 1')
		self.addTab(Shelf(self), 'Tab 2')
		self.addTab(Shelf(self), 'Tab 3')

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

class Shelf(QtGui.QScrollArea):
	def __init__(self, parent=None):
		super(Shelf, self).__init__(parent)
		self.setFrameStyle(QtGui.QFrame.NoFrame)
		self.verticalScrollBar().setSingleStep(32)
		self.verticalScrollBar().setPageStep(32)
		self.horizontalScrollBar().setSingleStep(32)
		self.horizontalScrollBar().setPageStep(32)

		self.setStyleSheet('''
		QScrollBar:vertical { background: rgb(80, 80, 80);}
		''')

		self.setObjectName('mayaShelfContentsScroll')
		self.setWidgetResizable(True)

		contents = QtGui.QWidget(self)
		contents.setObjectName('mayaShelfContents')
		self.setWidget(contents)

		self.shelfLayout = flowlayout.FlowLayout(contents)
		self.shelfLayout.setObjectName('shelfLayout')
		contents.setLayout(self.shelfLayout)
		self.shelfLayout.setSpacing(0)
		self.widget().setContentsMargins(2, 3, 0, 0)
		self.setAcceptDrops(True)
		self.highlight = QtGui.QRubberBand(QtGui.QRubberBand.Line, self)

		#Test code
		import random
		for i in range(random.randint(5, 25)):
			btn = ShelfButton()
			btn.setIconSize(QtCore.QSize(32, 32))
			btn.setMinimumSize(QtCore.QSize(32, 32))
			btn.setIcon(makeIcon(':/sphere.png'))
			btn.setText('test %s'%i)
			self.shelfLayout.addWidget(btn)

	def setToolBarArea(self, area):
		pass

	def setOrientation(self, orientation):
		if orientation == QtCore.Qt.Vertical:
			self.shelfLayout.setWrapOverflow(0)
		else:
			self.shelfLayout.setWrapOverflow(32)

	def dropEvent(self, event):
		self.highlight.hide()

		print 'Drop Index:', self.getIndexFrom(event.pos())
		#print event
		#print '\n'.join(event.mimeData().formats())

		if 'application/x-maya-data' in event.mimeData().formats():
			widget = event.source()
			control = widget.objectName()

			if cmds.shelfButton(control, q=True, ex=True):
				command = cmds.shelfButton(control, q=True, c=True)
				sType = cmds.shelfButton(control, q=True, sourceType=True)
				normal =  cmds.shelfButton(control, q=True, image=True)
				over = cmds.shelfButton(control, q=True, highlightImage=True)
				pressed = cmds.shelfButton(control, q=True, selectionImage=True)

				print control
				print command
				print normal

	def getIndexFrom(self, pos):
		widget = self.childAt(pos)
		if widget:
			index = self.shelfLayout.indexOf(widget)
			if index>=0:
				return index

		closest = (QWIDGETSIZE_MAX, None)
		for index in range(self.shelfLayout.count()):
			widget = self.shelfLayout.itemAt(index).widget()
			widgetPos = widget.geometry().center()
			assert isinstance(pos, QtCore.QPoint)
			distance = (widgetPos-pos).manhattanLength()
			if distance<closest[0] and distance<32+32:
				closest = (distance, widget)

		if closest[1] is not None:
			return self.shelfLayout.indexOf(closest[1])

		#Right side drop
		return -1

	def dragEnterEvent(self, event):
		if event.source().parent()==self.widget():
			event.setDropAction(QtCore.Qt.MoveAction)
		else:
			event.setDropAction(QtCore.Qt.CopyAction)
		event.accept()
		highlightIndex = self.getIndexFrom(event.pos())
		self.drawHighlight(highlightIndex)

	def dragMoveEvent(self, event):
		if event.source().parent()==self.widget():
			event.setDropAction(QtCore.Qt.MoveAction)
		else:
			event.setDropAction(QtCore.Qt.CopyAction)
		event.accept()
		highlightIndex = self.getIndexFrom(event.pos())
		self.drawHighlight(highlightIndex)

	def dragLeaveEvent(self, event):
		self.highlight.hide()


	def drawHighlight(self, index):
		if index==-1:
			item = self.shelfLayout.itemAt(self.shelfLayout.count()-1)
		else:
			item = self.shelfLayout.itemAt(index)

		if item is None:
			rect = self.widget().rect()
		else:
			rect = item.widget().geometry()

		if index!=-1:
			rect.setRight(rect.left()+1)
		else:
			rect.setLeft(rect.right()-1)

		self.highlight.setGeometry(rect)
		self.highlight.show()


	def load(self, path):
		pass

	def save(self, path):
		pass



class ShelfButton(QtGui.QToolButton):
	def __init__(self, parent=None):
		super(ShelfButton, self).__init__(parent)
		self.setAutoRaise(True)
		#self.setStyleSheet('QToolButton{margin: 0px 0px 0px 0px; border:none;}')

	def mouseMoveEvent(self, event):
		#print 'Mouse Move'
		if event.buttons() == QtCore.Qt.LeftButton:
			if not self.rect().contains(event.pos()):
				drag = QtGui.QDrag(self)
				data = QtCore.QMimeData()
				data.setText(self.text())
				data.setImageData(self.icon().pixmap(32, 32, self.icon().Normal, self.icon().On))
				drag.setMimeData(data)
				drag.setPixmap(QtGui.QPixmap.grabWidget(self))
				#drag.setPixmap(self.icon().pixmap(32, 32, self.icon().Normal, self.icon().On))
				drag.setHotSpot(QtCore.QPoint(22, 22))

				shelfButtons = set(cmds.lsUI(typ='shelfButton'))
				dropAction = drag.exec_(QtCore.Qt.MoveAction|QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
				new_buttons = list(set(cmds.lsUI(typ='shelfButton')).difference(shelfButtons))

				if len(new_buttons) == 1:
					button = new_buttons.pop()
					print 'Dropped button!', button

				else:
					print 'Dropped'
					#print dropAction
					#print drag.target()
					#print drag.target().objectName()

		super(ShelfButton, self).mouseMoveEvent(event)

class TrashButton(QtGui.QToolButton):
	def __init__(self, parent=None):
		super(TrashButton, self).__init__(parent)
		self.setStyleSheet('QToolButton{margin: -2px -2px -2px -2px; border:none;}')
		self.setIconSize(QtCore.QSize(32, 32))
		self.setIcon(QtGui.QIcon(':/smallTrash.png'))
		self.setAutoRaise(True)
		self.setAcceptDrops(True)
		self.setObjectName('shelfTrashBtn')

	def dragEnterEvent(self, event):
		event.setDropAction(QtCore.Qt.MoveAction)
		event.accept()

	def dragMoveEvent(self, event):
		event.setDropAction(QtCore.Qt.MoveAction)
		event.accept()



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
__author__ = 'Nathan'

import logging
import __main__

from ..lib import qt
from ..lib.qt import QtGui, QtCore
from ..lib.widgets import flowlayout
reload(flowlayout)

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

		self.addWidget(self.shelfOpts)
		self.addWidget(self.shelfTabs)
		self.setFloatable(False)

		self._last_state = (0, 0)
		self.setMinimumSize(QtCore.QSize(32, 32))

		#self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

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


	def sizeHint(self):
		if self.parent():
			area = self.parent().toolBarArea(self)
		else:
			area = 0
		if area == QtCore.Qt.LeftToolBarArea:
			return QtCore.QSize(64, 128)
		return QtCore.QSize(64, 64)

	def updateLayout(self, state=None):
		if state is None:
			state = self._last_state
		area, orientation = state


		self.shelfTabs.setToolBarArea(area)
		self.shelfTabs.setOrientation(orientation)
		self.shelfOpts.setOrientation(orientation)

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

class ShelfOptions(QtGui.QFrame):
	def __init__(self, parent=None):
		super(ShelfOptions, self).__init__(parent)
		self.optionsMenu = QtGui.QToolButton(self)
		self.switcherMenu = QtGui.QToolButton(self)

	def setOrientation(self, orientation):
		if self.layout():
			#Shortcut if direction hasnt changed
			hbox = isinstance(self.layout(), QtGui.QHBoxLayout)
			if orientation == QtCore.Qt.Vertical and hbox:
				return
			if orientation == QtCore.Qt.Horizontal and not hbox:
				return

			#Remove widgets and delete layout before creating a new oen
			for child in self.layout().children():
				self.layout().removeWidget(child)
			self.layout().deleteLater()

		#Create layout
		if orientation == QtCore.Qt.Vertical:
			self.setLayout(QtGui.QHBoxLayout(self))
		else:
			self.setLayout(QtGui.QVBoxLayout(self))

		#Parent widgets
		self.layout().setContentsMargins(2, 2, 2, 2)
		self.layout().setSpacing(2)
		self.layout().addWidget(self.switcherMenu)
		self.layout().addWidget(self.optionsMenu)

class ShelfTabs(QtGui.QTabWidget):
	toolButtonStyleChanged = QtCore.Signal(QtCore.Qt.ToolButtonStyle)
	def __init__(self, parent=None):
		super(ShelfTabs, self).__init__(parent)

		trashBtn = TrashButton(self)
		self.setCornerWidget(trashBtn)
		self.setAcceptDrops(True)
		self.highlight = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)

		#Test code
		self.addTab(Shelf(self), 'Tab 1')
		self.addTab(Shelf(self), 'Tab 2')
		self.addTab(Shelf(self), 'Tab 3')
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



class Shelf(QtGui.QScrollArea):
	toolButtonStyleChanged = QtCore.Signal(QtCore.Qt.ToolButtonStyle)
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
			btn.setText('test longer name %s\nsecond line of text\nthird now...'%i)
			self.shelfLayout.addWidget(btn)
			self.toolButtonStyleChanged.connect(btn.setToolButtonStyle)

	def load(self, path):
		pass

	def save(self, path):
		pass

	def setToolBarArea(self, area):
		pass

	def setOrientation(self, orientation):
		if orientation == QtCore.Qt.Vertical:
			self.shelfLayout.setWrapOverflow(0)
		else:
			self.shelfLayout.setWrapOverflow(32)

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

			if index == self.shelfLayout.count()-1:
				maxDistance = 0
			else:
				maxDistance = 64

			if distance<closest[0] and distance<maxDistance:
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

	def dropEvent(self, event):
		self.highlight.hide()

		print 'Drop Index:', self.getIndexFrom(event.pos())
		#print event
		#print '\n'.join(event.mimeData().formats())

		if 'application/x-maya-data' in event.mimeData().formats():
			widget = event.source()

			controlPath = qt.widgetToMayaName(widget).split('|')

			control = controlType = None
			for i in range(len(controlPath)):
				try:
					path = '|'.join(controlPath[:-i])
					print path
					controlType = cmds.objectTypeUI(path)
					control = path
					break
				except:
					continue


			btn = ShelfButton.createFromMaya(event.mimeData(), control, controlType)

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
					print 'Dropped', dropAction
					#print dropAction
					#print drag.target()
					#print drag.target().objectName()

		super(ShelfButton, self).mouseMoveEvent(event)


	@classmethod
	def createFromMaya(cls, data, control, controlType):
		btn = cls()
		if controlType == 'shelfButton':
			command = cmds.shelfButton(control, q=True, c=True)
			sType = cmds.shelfButton(control, q=True, sourceType=True)
			normal =  cmds.shelfButton(control, q=True, image=True)
			over = cmds.shelfButton(control, q=True, highlightImage=True)
			pressed = cmds.shelfButton(control, q=True, selectionImage=True)

			btn.setText(command)
		elif controlType == 'cmdScrollFieldExecuter':
			command = data.text()
			sType = cmds.cmdScrollFieldExecuter(control, q=True, sourceType=True)

		else:
			log.warn('Unsuported drag and drop source: %s - %s'%(controlType, control))


		return cls()






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
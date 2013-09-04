__author__ = 'Nathan'

import random
import logging
import __main__

from functools import partial

from ..core import qt
from ..core.qt import QtGui, QtCore
from ..core.widgets import flowlayout
from . import shelfbutton
from . import util


reload(shelfbutton)
reload(flowlayout)

import maya.cmds as cmds

log = logging.getLogger(__name__)
QWIDGETSIZE_MAX = 16777215

class Shelf(QtGui.QScrollArea):
	toolButtonStyleChanged = QtCore.Signal(QtCore.Qt.ToolButtonStyle)
	def __init__(self, parent=None):
		super(Shelf, self).__init__(parent)
		self.setFrameStyle(QtGui.QFrame.NoFrame)

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
		self.shelfLayout.setVerticalSpacing(4)
		self.widget().setContentsMargins(2, 2, 0, 2)
		self.setAcceptDrops(True)
		self.highlight = QtGui.QRubberBand(QtGui.QRubberBand.Line, self)

		self.setOrientation(QtCore.Qt.Horizontal)

		#Test code
		icons = [':/sphere.png', ':/cube.png', ':/cylinder.png', ':/cone.png', ':/plane.png', ':/torus.png']
		for i in range(random.randint(1, 100)):
			btn = shelfbutton.ShelfButton()
			btn.setIconSize(QtCore.QSize(32, 32))
			btn.setMinimumSize(QtCore.QSize(32, 32))
			btn.setIcon(util.makeIcon(random.choice(icons)))
			btn.setText('test longer name %s\nsecond line of text\nthird now...'%i)
			self.shelfLayout.addWidget(btn)
			self.toolButtonStyleChanged.connect(btn.setToolButtonStyle)

	@classmethod
	def createFromPath(cls, path):
		shelf = cls()
		shelf.load(path)
		return shelf

	def load(self, path):
		pass

	def save(self, path):
		pass

	def setOrientation(self, orientation):
		self.orientation = orientation
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

		if self.orientation == QtCore.Qt.Horizontal:
			if index!=-1:
				rect.setRight(rect.left()+1)
			else:
				rect.setLeft(rect.right()-1)
		else:
			if index!=-1:
				rect.setBottom(rect.top()+1)
			else:
				rect.setTop(rect.bottom()-1)

		self.highlight.setGeometry(rect)
		self.highlight.show()

	def dropEvent(self, event):
		self.highlight.hide()
		dropIndex = self.getIndexFrom(event.pos())

		print 'Drop Index:',dropIndex
		#print event
		#print '\n'.join(event.mimeData().formats())

		if 'application/x-maya-data' in event.mimeData().formats():
			widget = event.source()

			controlPath = qt.widgetToMayaName(widget).split('|')

			control = controlType = None
			for i in range(len(controlPath)):
				try:
					if i:
						path = '|'.join(controlPath[:-i])
					else:
						path = '|'.join(controlPath)
					controlType = cmds.objectTypeUI(path)
					control = path
					break
				except:
					continue


			btn = shelfbutton.ShelfButton.createFromMaya(event.mimeData(), control, controlType)
			self.shelfLayout.insertWidget(dropIndex, btn)

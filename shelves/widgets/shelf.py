__author__ = 'Nathan'

import logging
import __main__

from functools import partial

from ...lib import qt
from ...lib.qt import QtGui, QtCore
from ...lib.widgets import flowlayout
from . import buttons
reload(flowlayout)

import maya.cmds as cmds

log = logging.getLogger(__name__)
QWIDGETSIZE_MAX = 16777215

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
			btn = buttons.ShelfButton()
			btn.setIconSize(QtCore.QSize(32, 32))
			btn.setMinimumSize(QtCore.QSize(32, 32))
			btn.setIcon(buttons.makeIcon(':/sphere.png'))
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


			btn = buttons.ShelfButton.createFromMaya(event.mimeData(), control, controlType)
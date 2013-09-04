__author__ = 'Nathan'

import random
import logging
import __main__

from functools import partial

from ..core import qt
from ..core.qt import QtGui, QtCore
from . import util

import maya.cmds as cmds


log = logging.getLogger(__name__)
QWIDGETSIZE_MAX = 16777215

class ShelfButton(QtGui.QToolButton):
	def __init__(self, parent=None):
		super(ShelfButton, self).__init__(parent)
		self.setAutoRaise(True)
		self.setIconSize(QtCore.QSize(32, 32))
		self.setMinimumSize(QtCore.QSize(32, 32))

		'''
		Data:
			icon paths (normal, hover, press)

		'''

		#color = ['50, 0, 50, 100', '50, 0, 0, 100', '0, 0, 50, 100', '0, 50, 0, 100', '50, 50, 0, 100']
		#self.setStyleSheet('QToolButton{background: rgba(%s);}'%random.choice(color))

		self.labelRenderer = QtGui.QTextDocument(self)
		self.labelRenderer.setDocumentMargin(0)

		if random.randint(0, 4)>0:
			self.setPopupMode(random.choice([self.MenuButtonPopup, self.DelayedPopup, self.InstantPopup]))
			self.setMenu(QtGui.QMenu(self))
			self.menu().addAction('test 1')
			self.menu().addAction('test 2')
			self.menu().addAction('test 3')
			self.setCursor(QtGui.QCursor(QtGui.QPixmap(':/rmbMenu.png'), 6, 2))
		font = QtGui.QFont()
		font.setPointSize(8)
		font.setFamily('Segoe UI')
		self.labelRenderer.setDefaultFont(font)

	def enterEvent(self, event):
		QtGui.QToolButton.enterEvent(self, event)
		if not self.autoRaise():
			self.update()

	def leaveEvent(self, event):
		QtGui.QToolButton.leaveEvent(self, event)
		if not self.autoRaise():
			self.update()

	def paintEvent(self, event):
		painter = QtGui.QStylePainter(self)
		opt = QtGui.QStyleOptionToolButton()
		self.initStyleOption(opt)

		if opt.state & QtGui.QStyle.State_MouseOver:
			opt.state |= QtGui.QStyle.State_AutoRaise

		painter.drawComplexControl(QtGui.QStyle.CC_ToolButton, opt)

		#rectf = QtCore.QRectF(self.rect())
		#Set up the label documents
		#self.labelRenderer.setHtml('<span style="color:#00ff00;background:rgba(0, 0, 255, 70);">Test String!</span>')
		#self.labelRenderer.setTextWidth(rectf.width())
		#Align the label based on document size
		#self.labelRenderer.size()
		#self.labelRenderer.drawContents(painter, rectf)

		painter.end()

	def mouseMoveEvent(self, event):
		#print 'Mouse Move'
		if event.buttons() == QtCore.Qt.MiddleButton:
			if not self.rect().contains(event.pos()):
				#self.hide()
				#self.parent().layout().removeWidget(self)
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
			annotation = cmds.shelfButton(control, q=True, annotation=True)
			sType = cmds.shelfButton(control, q=True, sourceType=True)
			normal =  cmds.shelfButton(control, q=True, image=True)
			over = cmds.shelfButton(control, q=True, highlightImage=True)
			pressed = cmds.shelfButton(control, q=True, selectionImage=True)

			normal = util.resolvePath(normal)
			over = util.resolvePath(over)


			btn.setIcon(util.makeIcon(normal, over or None))
			btn.setText(command)
			btn.setToolTip(annotation or command)

		elif controlType == 'cmdScrollFieldExecuter':
			command = data.text()
			sType = cmds.cmdScrollFieldExecuter(control, q=True, sourceType=True)

			btn.setText(command)
			btn.setToolTip(command)

			if sType == 'python':
				btn.setIcon(util.makeIcon(':/pythonFamily.png'))
			else:
				btn.setIcon(util.makeIcon(':/commandButton.png'))

		else:
			log.warn('Unsuported drag and drop source: %s - %s'%(controlType, control))

		return btn


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



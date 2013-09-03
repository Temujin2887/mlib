from .. import qt
from ..qt import QtGui, QtCore

class FlowLayout(QtGui.QLayout):
	"""
	Port of the Qt 4.X flow layout example
	"""
	def __init__(self, parent=None, margin=0, spacing=-1):
		super(FlowLayout, self).__init__(parent)

		if parent is not None:
			self.setMargin(margin)

		self.setSpacing(spacing)
		self.itemList = []
		self.wrapOverflow = 0

	def __del__(self):
		self.takeAll()

	def takeAll(self):
		item = self.takeAt(0)
		while item:
			item = self.takeAt(0)

	def addItem(self, item):
		if item.widget() and hasattr(item.widget(), '_temp_insert_index'):
			index = item.widget()._temp_insert_index
			if index<0:
				index = len(self.itemList)+index+1
			print index
			self.itemList.insert(index, item)
		else:
			self.itemList.append(item)

	def insertWidget(self, index, widget):
		widget._temp_insert_index = index
		self.addWidget(widget)
		del widget._temp_insert_index

	def count(self):
		return len(self.itemList)

	def itemAt(self, index):
		if 0 <= index < len(self.itemList):
			return self.itemList[index]
		return None

	def takeAt(self, index):
		if 0 <= index < len(self.itemList):
			return self.itemList.pop(index)
		return None

	def expandingDirections(self):
		return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

	def hasHeightForWidth(self):
		return True

	def heightForWidth(self, width):
		height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
		return height

	def setGeometry(self, rect):
		QtGui.QLayout.setGeometry(self, rect)
		self.doLayout(rect, False)

	def setWrapOverflow(self, overflow):
		self.wrapOverflow = overflow
		self.doLayout(self.geometry(), False)

	def sizeHint(self):
		return self.minimumSize()

	def minimumSize(self):
		size = QtCore.QSize()

		for item in self.itemList:
			size = size.expandedTo(item.minimumSize())

		size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
		return size

	def doLayout(self, rect, testOnly):
		x = rect.x()
		y = rect.y()
		lineHeight = 0

		for item in self.itemList:
			spaceX = self.spacing()
			spaceY = self.spacing()
			nextX = x + spaceX + item.sizeHint().width()
			if nextX - spaceX - self.wrapOverflow > rect.right() and lineHeight > 0:
				x = rect.x()
				y = y + lineHeight + spaceY
				nextX = x + spaceX + item.sizeHint().width()
				lineHeight = 0

			if not testOnly:
				item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

			x = nextX
			lineHeight = max(lineHeight, item.sizeHint().height())

		return y + lineHeight - rect.y()
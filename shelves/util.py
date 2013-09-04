__author__ = 'Nathan'

import os
from ..core.qt import QtGui, QtCore

def resolvePath(path):
	if os.path.isabs(path):
		return path
	if path.startswith(':/'):
		return path
	return ':/'+path

def makeIcon(path, over=None, resize=None):
	pixmap_normal = QtGui.QPixmap(path)
	if over is None:
		pixmap_over = pixmap_normal.copy()
		painter = QtGui.QPainter(pixmap_over)

		alpha = QtGui.QPixmap(pixmap_over.size())
		alpha.fill(QtGui.QColor(100, 100, 100))
		pixmap_dode = pixmap_normal.copy()
		pixmap_dode.setAlphaChannel(alpha)

		painter.setCompositionMode(painter.CompositionMode_ColorDodge)
		painter.drawPixmap(0, 0, pixmap_dode)

		painter.end()
	else:
		pixmap_over = QtGui.QPixmap(over)

	if isinstance(resize, (list, tuple)):
		assert len(resize) == 2
		pixmap_normal = pixmap_normal.scaled(resize[0], resize[1], QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
		pixmap_over = pixmap_over.scaled(resize[0], resize[1], QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
		#pixmap_pressed = pixmap_pressed.scaled(resize[0], resize[1], QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

	icon = QtGui.QIcon()
	icon.addPixmap(pixmap_normal, icon.Normal, icon.On)
	icon.addPixmap(pixmap_over, icon.Active, icon.On)
	return icon
__author__ = 'Nathan'

import os
from ..core.qt import QtGui, QtCore

def resolvePath(path):
	if not path:
		return path
	
	if os.path.isabs(path):
		return path
	if path.startswith(':/'):
		return path
	
	folder, sep, path = os.path.normpath(path).rpartition(os.path.sep)
	
	for icon_dir in os.environ['XBMLANGPATH'].split(';'):
		if not icon_dir or not os.path.isdir(icon_dir):
			continue
		icon_dir = os.path.normpath(icon_dir)
		
		for root, folders, files in os.walk(icon_dir):
			if folder and not root.endswith(os.path.sep+folder):
				continue
			
			if path in files:
				return os.path.join(root, path)
	
	return path

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

__author__ = 'Nathan'

from ..core import qt
from ..core.qt import QtGui, QtCore

import maya.cmds as cmds


#Fix for the clipboard bug when coming from Wing/PyCharm
class ScriptEditorFilter(QtCore.QObject):
	def eventFilter(self, obj, event):
		if event == QtGui.QKeySequence.Paste and event.type() == QtCore.QEvent.KeyPress:
			if isinstance(obj, QtGui.QWidget):
				if obj.objectName().startswith('cmdScrollFieldExecuter'):
					print 'Paste:', type(obj)
					#Paste clipboard text this way, more reliable than Maya's check.
					maya_widget = qt.widgetToPath(obj)
					cmds.cmdScrollFieldExecuter(maya_widget, e=True, it=QtGui.qApp.clipboard().text())
					return True
		return False

def main():
	if hasattr(QtGui.qApp, '_clipboard_fix'):
		QtGui.qApp.removeEventFilter(QtGui.qApp._clipboard_fix)
		del QtGui.qApp._clipboard_fix
	QtGui.qApp._clipboard_fix = ScriptEditorFilter()
	QtGui.qApp.installEventFilter(QtGui.qApp._clipboard_fix)
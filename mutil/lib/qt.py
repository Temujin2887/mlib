__author__ = 'Nathan'


import os
import sys
import time
import logging
import subprocess

from functools import partial, update_wrapper

qt_lib = None
has_maya = False

try:
	#Attempt to load in PyQt first, as it's the preferred library as of 2014 still.
	import sip
	sip.setapi('QString', 2)
	sip.setapi('QVariant', 2)

	from PyQt4 import QtGui, QtCore, uic
	qt_lib = 'pyqt'

except ImportError:
	#PyQt failed to load, give PySide a shot
	import shiboken
	import PySide
	from PySide import QtGui, QtCore
	import pysideuic as uic
	QtCore.pyqtSignal = QtCore.Signal
	QtCore.pyqtSlot = QtCore.Slot

	qt_lib = 'pyside'


try:
	#Try to load maya...
	import maya.cmds as cmds
	if cmds.internalVar(upd=True) is None:
		raise SystemError('Standalone uninitialized')

	import maya
	import maya.mel as mel
	import maya.OpenMaya as api
	import maya.OpenMayaUI as apiUI

	#Define Callback function to handle our callback wrapper
	mel.eval("global proc Callback(string $description){};")
except (ImportError, SystemError, AttributeError):
	has_maya = False


def loadUiFile(path):
	"""
	Load a designer UI xml file in

	:param path: Either the relative path to the module calling this function,
	 or a full path to a file on disk. Can be a partial path.
	:type path:
	"""
	pass





###-----------------------------------###
###Convience functions to help with Qt###
###-----------------------------------###
def getFocusWidget():
	"""
	Get the currently focused widget

	:return: Widget with focus currently
	:rtype: QtGui.QWidget or None
	"""
	return QtGui.qApp.focusWidget()


def getWidgetAtMouse():
	"""
	Get the widget under the mouse

	:return: QtGui.QWidget or None
	"""
	currentPos = QtGui.QCursor().pos()
	widget = QtGui.qApp.widgetAt(currentPos)
	return widget


def qrcToPythonRc(path, target):
	"""
	Given a path to a qrc file, create the target file
	This also tries to checkout the file from perforce if it can.

	:param path: Qrc file path to compile
	:type path: str
	:param target: Target path for compiled python RC file
	:type target: str
	"""
	qt_lib_root = os.path.dirname(QtGui.__file__)
	rcc_exe = os.path.join(qt_lib_root, 'bin', 'pyrcc4.exe')
	proc = subprocess.Popen([rcc_exe, path, '-o', target], shell=True)
	proc.wait()


def wrapinstance(ptr, base=None):
	"""
	Utility to convert a pointer to a Qt class instance

	:param ptr: Pointer to QObject in memory
	:type ptr: long or Swig instance
	:param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
	:type base: QtGui.QWidget
	:return: QWidget or subclass instance
	:rtype: QtGui.QWidget
	"""
	if ptr is None:
		return None
	ptr = long(ptr)  #Ensure type
	if qt_lib == 'pyqt':
		base = QtCore.QObject
		return sip.wrapinstance(long(ptr), base)
	elif qt_lib == 'pyside':
		#Pyside makes this a pain for us, since unlike Pyqt it does not return the "best" matching class automatically
		if base is None:
			qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
			metaObj = qObj.metaObject()
			cls = metaObj.className()
			superCls = metaObj.superClass().className()
			if hasattr(QtGui, cls):
				base = getattr(QtGui, cls)
			elif hasattr(QtGui, superCls):
				base = getattr(QtGui, superCls)
			else:
				base = QtGui.QWidget
		return shiboken.wrapInstance(long(ptr), base)


def unwrapinstance(obj):
	"""
	Utility to convert a Qt class instance to a pointer

	:param obj: Object to unwrap
	:type obj: Qt Object
	:return: Unwrapped instance pointer
	:rtype: long
	"""
	if obj is None:
		return
	if qt_lib == 'pyqt':
		return sip.unwrapinstance(obj)
	elif qt_lib == 'pyside':
		#TODO: Verify this actually works, from some reading around it most likely doesn't currently...
		return shiboken.unwrapinstance(obj)


###-----------------------------------------------------###
###Maya specific helpers, won't function outside of maya###
###-----------------------------------------------------###
def toQtObject(mayaName):
	"""
	Given the name of a Maya UI element of any type, return the corresponding QWidget or QAction.
	If the object does not exist, returns None

	:param mayaName: Maya name to get a Qt widget for
	:type mayaName: str
	:return: Widget Object
	:rtype: QtCore.QWidget
	"""
	ptr = apiUI.MQtUtil.findControl(mayaName)
	if ptr is None:
		ptr = apiUI.MQtUtil.findLayout(mayaName)
		if ptr is None:
			ptr = apiUI.MQtUtil.findMenuItem(mayaName)
	return wrapinstance(ptr)


def getMayaWindow():
	"""
	Get the maya main window as a QMainWindow instance

	:return: MainWindow instance
	:rtype: QtGui.QMainWindow
	"""
	try:
		ptr = apiUI.MQtUtil.mainWindow()
		return wrapinstance(ptr)
	except Exception:
		return None


def widgetToMayaName(widget):
	"""
	Return the maya full ui path to the given Qt widget

	:param widget: Qt widget to get a Maya path for if possible
	:type widget: QtGui.QWiget or QtCore.QObject
	:return: Maya UI path, or None
	:rtype: str
	"""
	return apiUI.MQtUtil.fullName(unwrapinstance(widget))


def getParentWidget(widget):
	"""
	Take a given QWidget and return it's Maya UI parent

	:param widget: widget to get parent for
	:type widget: QtGui.QWidget
	:return: Parent widget or None
	:rtype: QtGui.QWidget
	"""
	ptr = apiUI.MQtUtil.getParent(unwrapinstance(widget))
	return wrapinstance(long(ptr))
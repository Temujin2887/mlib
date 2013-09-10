__author__ = 'Nathan'

import os
import sys
import time
import logging
import inspect
import subprocess
import __main__

from functools import partial, update_wrapper

log = logging.getLogger(__name__)


#Find the best way to provide a switch for the order....
load_order = ['pyqt', 'pyside']
#load_order = ['pyside', 'pyqt']

#We have to import these the "hard" way rather than with __import__ because
# some people like something called "Auto-Completion" :)
qt_lib = None
for library in load_order:
	if library == 'pyside':
		try:
			from PySide import QtGui, QtCore
			import shiboken
			import pysideuic as uic
			import xml.etree.cElementTree as xml
			import cStringIO as StringIO
		except ImportError as e:
			continue

		try: from PySide import QtDeclarative
		except ImportError: pass
		try: from PySide import QtMultimedia
		except: pass
		try: from PySide import QtNetwork
		except: pass
		try: from PySide import QtOpenGL
		except: pass
		try: from PySide import QtOpenVG
		except: pass
		try: from PySide import QtScript
		except: pass
		try: from PySide import QtScriptTools
		except: pass
		try: from PySide import QtSql
		except: pass
		try: from PySide import QtSvg
		except: pass
		try: from PySide import QtWebKit
		except: pass
		try: from PySide import QtXml
		except: pass
		try: from PySide import QtXmlPatterns
		except: pass
		try: from PySide import phonon
		except: pass
		try: from PySide import QtUiTools
		except: pass 
		try:
			from PySide.phonon import Phonon
			sys.modules[__name__+'.phonon'] = phonon
		except: pass

		QtCore.pyqtSignal = QtCore.Signal
		QtCore.pyqtSlot = QtCore.Slot
		QtCore.pyqtProperty = QtCore.Property

		qt_lib = library
		break

	elif library == 'pyqt':
		try:
			import sip
		except:
			continue
		try:
			sip.setapi('QDate', 2)
			sip.setapi('QDateTime', 2)
			sip.setapi('QString', 2)
			sip.setapi('QTextStream', 2)
			sip.setapi('QTime', 2)
			sip.setapi('QUrl', 2)
			sip.setapi('QVariant', 2)
		except ValueError:
			log.exception('Failed to set sip api version for PyQt4, have you imported it before this?')

		try:
			from PyQt4 import QtGui, QtCore, uic
		except ImportError:
			continue

		try: from PyQt4 import QtDeclarative
		except ImportError: pass
		try: from PyQt4 import QtMultimedia
		except: pass
		try: from PyQt4 import QtNetwork
		except: pass
		try: from PyQt4 import QtOpenGL
		except: pass
		try: from PyQt4 import QtOpenVG
		except: pass
		try: from PyQt4 import QtScript
		except: pass
		try: from PyQt4 import QtScriptTools
		except: pass
		try: from PyQt4 import QtSql
		except: pass
		try: from PyQt4 import QtSvg
		except: pass
		try: from PyQt4 import QtWebKit
		except: pass
		try: from PyQt4 import QtXml
		except: pass
		try: from PyQt4 import QtXmlPatterns
		except: pass
		try: from PyQt4 import phonon
		except: pass
		try:
			from PyQt4.phonon import Phonon
			sys.modules[__name__+'.phonon'] = phonon
		except: pass

		QtCore.Signal = QtCore.pyqtSignal
		QtCore.Slot = QtCore.pyqtSlot
		QtCore.Property = QtCore.pyqtProperty

		qt_lib = library
		break


try:
	#Try to load maya...
	import maya.cmds as cmds

	if cmds.internalVar(upd=True) is None:
		raise SystemError('Standalone uninitialized')

	import maya
	import maya.mel as mel
	import maya.OpenMaya as om
	import maya.OpenMayaUI as omUI

	has_maya = True
except (ImportError, SystemError, AttributeError):
	has_maya = False


def loadUiFile(ui_path, appname=None, manage_settings=True):
	"""
	Load a designer UI xml file in

	:param ui_path: Path to UI file.
		``ui_path`` be a partial path relative to the file calling :py:func:`.loadUiFile`.
		It is also not necessary to include the `.ui` extension.

	:type ui_path: str
	:return: Window Class defined by the input UI file
	"""
	#Add extension if missing..
	if not ui_path.endswith('.ui'):
		ui_path += '.ui'

	if not os.path.isfile(ui_path):
		#Resolve partial path into full path based on the call stack
		frame = inspect.currentframe().f_back  #Back up one from the current frame
		modpath = frame.f_code.co_filename  #Grab the filename from the code object
		base_directory = os.path.dirname(modpath)

		resolvePath = os.path.join(base_directory, ui_path)

		if os.path.isfile(resolvePath):
			ui_path = resolvePath
		else:
			raise ValueError('Could not locate UI file at path: %s' % ui_path)

	#Load the form class, and establish what the base class for the top level is in order to sub-class it
	if qt_lib == 'pyqt':
		#This step is easy with PyQt
		with open(ui_path, 'r') as f:
			form_class, base_class = uic.loadUiType(f)

	elif qt_lib == 'pyside':
		"""
		Pyside lacks the "loadUiType" command :(
		"""
		loader = QtUiTools.QUiLoader()

		f = QtCore.QFile(ui_path)
		f.open(f.ReadOnly)
		try:
			form_class, base_class = loader.load(f), QtGui.QWidget
		finally:
			f.close()

	if False: #Type hinting for pycharm/wing
		base_class = QtGui.QWidget

	class FormClass(DesignerForm, form_class, base_class): pass
	if not appname:
		appname, ext = os.path.splitext(os.path.basename(ui_path))

	FormClass.setAppName(appname)
	FormClass.setUiPath(ui_path)
	FormClass.setSettingsManaged(manage_settings)
	return FormClass


class DesignerForm(object):
	"""
	Base class for widgets loaded with loadUiType.
	This class provides convenience functions, and manages a few of the more specific features of the loadUiFile function.
	"""
	__ui_path = None
	__app_name = None
	__managed = True
	__unmanaged_widgets = []

	def __init__(self, parent=None):
		super(DesignerForm, self).__init__(parent)
		self.setupUi(self) #Now run the setupUi function for the user
		QtGui.qApp.aboutToQuit.connect(self.close)

		#Store initial settings for reset
		self.__initial_settings = InitialSettings()
		saveLoadSettings(self, settings=self.__initial_settings)

		#Create a settings object for the user if they have us managing their settings
		if self.getSettingsManaged():
			self.__has_loaded = False
			self.settings = getSettings(self.getAppName(), self)

	def showEvent(self, event):
		#If we manage settings, load the state on first show
		if not self.__has_loaded and self.getSettingsManaged():
			self.loadSettings()
			self.__has_loaded = True

	def closeEvent(self, event):
		#If we manage settings save the settings on close
		if self.getSettingsManaged():
			self.saveSettings()

	def close(self):
		"""
		Slight tweak to the default close function, cleans up the window to avoid memory leaking.

		.. todo::
			Investigate if this is something people actually want, it seems safer this way, but I'm paranoid.

		"""
		QtGui.QWidget.close(self)
		if isValid(self):
			self.deleteLater()
		try:
			del self.__initial_settings
		except AttributeError:
			pass

	def setUnmanagedWidgets(self, widgets):
		"""
		Set a new list of managed widgets

		:param widgets: Widgets to not manage
		:type widgets: list of QObjects or objectName's
		"""
		self.__unmanaged_widgets = widgets[:]

	def getUnmanagedWidgets(self):
		return self.__unmanaged_widgets

	def saveSettings(self, ignore=None):
		"""

		:param ignore:
		"""
		if self.getSettingsManaged() and ignore is None:
			ignore = self.getUnmanagedWidgets()

		saveLoadSettings(self, ignore)

	def loadSettings(self, ignore=None):
		"""

		:param ignore:
		"""
		if self.getSettingsManaged() and ignore is None:
			ignore = self.getUnmanagedWidgets()

		saveLoadSettings(self, ignore, False)

	def resetSettings(self, ignore=None, skipGeometry=False, skipWindowState=False):
		"""
		Reset the window to it's "initial" state from when the UI for was loaded


		:param ignore:
		:param skipGeometry:
		:param skipWindowState:
		"""
		log.info('Resetting window settings!')
		settings = InitialSettings(self.__initial_settings.items())

		if not skipGeometry:
			geom = settings.value('geometry', None)
			if geom:
				settings.setValue('geometry', geom.moveTo(self.geometry().topLeft()))

		if self.getSettingsManaged() and ignore is None:
			ignore = self.getUnmanagedWidgets()

		saveLoadSettings(self, ignore=ignore, save=False, settings=self.__initial_settings,
		                 skipGeometry=skipGeometry, skipWindowState=skipWindowState)

	def saveWindowState(self):
		"""
		Save position/size of window
		"""
		saveLoadSettings(self, windowStateOnly=True)

	def loadWindowState(self):
		"""
		Load position/size of window
		"""
		saveLoadSettings(self, save=False, windowStateOnly=True)
	
	

	@classmethod
	def setAppName(cls, appname):
		cls.__app_name = appname

	@classmethod
	def getAppName(cls):
		return cls.__app_name

	@classmethod
	def setUiPath(cls, path):
		cls.__ui_path = path

	@classmethod
	def getUiPath(cls):
		return cls.__ui_path

	@classmethod
	def setSettingsManaged(cls, state):
		cls.__managed = state

	@classmethod
	def getSettingsManaged(cls):
		return cls.__managed

	@classmethod
	def showUI(cls, *args, **kwargs):
		"""
		Show a single instance of this form class, closes any previous instances regardless of reloads
		All arguments pass through to the base class.

		.. todo::
			Implement multi-instance window support for windows that want it.
		"""
		ukey = __name__ + '_loadUiWindows'
		windows = __main__.__dict__.setdefault(ukey, {})

		ui_path = cls.getUiPath()
		widget = windows.get(ui_path)
		closeAndCleanup(widget)

		windows[ui_path] = cls(*args, **kwargs)
		windows[ui_path].show()
		return windows[ui_path]

	@classmethod
	def closeUI(cls):
		"""
		Close the visible instance of this form class
		"""
		widget = cls.getVisibleInstance()
		closeAndCleanup(widget)

	@classmethod
	def getVisibleInstance(cls, create=False):
		"""
		Get the visible instance of this form class.
		If create is True, and this window does not already exists,
		it will return the result of showUI with no arguments.

		:param create: Create this ui if none exists
		:type create: bool
		:return: The visible instance if one exists
		:rtype: :py:class:`.DesignerForm` or None
		"""
		ukey = __name__ + '_loadUiWindows'
		windows = __main__.__dict__.setdefault(ukey, {})
		widget = windows.get(cls.getUiPath())
		if isValid(widget) and widget.isVisible():
			return widget
		if create:
			return cls.showUI()
		return None

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
		return shiboken.getCppPointer(obj)


def isValid(widget):
	"""
	Check if a widget is valid in the backend

	:param widget: QtGui.QWidget
	:return: True if the widget still has a c++ object
	:rtype: bool
	"""
	if widget is None:
		return False

	if qt_lib == 'pyqt':
		if sip.isdeleted(widget):
			return False
	elif qt_lib == 'pyside':
		if not shiboken.isValid(widget):
			return False
	return True


def closeAndCleanup(widget):
	"""
	Call close and deleteLater on a widget safely.

	.. note::
		Skips the close call if the widget is already not visible.

	:param widget: Widget to close and delete
	:type widget: QtGui.QWidget
	"""
	if isValid(widget):
		if widget.isVisible():
			widget.close()
		widget.deleteLater()


#Settings management
def getSettings(appName, unique=False, version=None):
	"""
	Helper to get a settings object for a given app-name
	It uses INI settings format for Maya, and registry format for stand-alone tools.
	Try to ensure that the appName provided is unique, as overlapping appNames
	will try to load/overwrite each others settings file/registry data.

	:param appName: string -- Application name to use when creating qtSettings ini file/registry entry.
	:return: QtCore.QSettings -- Settings object
	"""
	ukey = __name__ + '_QSettings'
	if not unique and (appName, version) in __main__.__dict__.setdefault(__name__+'_settings', {}):
		return __main__.__dict__[ukey][(appName, version)]

	if has_maya:
		settingsPath = os.path.join(cmds.internalVar(upd=True), 'mlib_settings', appName+'.ini')
		settingsPath = os.path.normpath(settingsPath)

		settings = QtCore.QSettings(settingsPath, QtCore.QSettings.IniFormat)
		settings.setParent(getMayaWindow())
	else:
		settings = QtCore.QSettings('MLib', appName)

	if not unique:
		__main__.__dict__[ukey][(appName, version)] = settings
	elif isinstance(unique, QtCore.QObject):
		settings.setParent(unique)

	if version is not None:
		if float(settings.value('__version__', version))<version:
			settings.clear()
		settings.setValue('__version__', version)
	return settings


def saveLoadSettings(widget, ignore=None, save=True, windowStateOnly=False, skipGeometry=False, skipWindowState=None,
                     settings=None):
	"""
	Save/Load state for a widget and it's sub-widgets

	:param widget: Widget to save/load state for
	:type widget: QtGui.QWidget
	:param ignore: widgets to ignore
	:type ignore: list
	:param save: Save if True, load if False
	:type save: bool
	:param windowStateOnly: Save/Load window state only?
	:type windowStateOnly: bool
	:param skipGeometry: Skip geometry when saving/loading?
	:type skipGeometry: bool
	:param settings: Optional QSettings object to save/load from instead of the default
	:type settings: QSettings or InitialSettings
	"""
	if settings is None:
		try:
			settings = widget.settings
		except AttributeError:
			log.exception(
				'Unable to get settings object from widget and no settings object provided... Unable to save settings!\n')
			return

	if skipWindowState is None:
		skipWindowState = skipGeometry

	if not hasattr(widget, 'saveState'):
		skipWindowState = True

	if save:
		if not skipGeometry:
			settings.setValue('geometry', widget.geometry())
		if not skipWindowState:
			settings.setValue('windowState', widget.saveState())
	else:
		if not skipGeometry:
			geom = settings.value('geometry', None)
			if geom:
				widget.setGeometry(geom)

		if not skipWindowState and hasattr(widget, 'restoreState'):
			widget.restoreState(settings.value('windowState', widget.saveState()))

	if windowStateOnly:
		return

	children = widget.findChildren(QtGui.QWidget)
	ignore = ignore or []
	for child in children:
		if child in ignore or child.objectName() in ignore:
			log.debug('Skipping ignored widget: %s %s'%(repr(child.objectName()), child))
			continue

		if not child.objectName():
			log.debug('Cannot save child widget, it has no objectName! %s'%child)
			continue

		key = child.objectName()
		saveLoadState(settings, child, key, save)


def saveLoadState(settings, widget, key=None, save=True):
	"""
	How to store/load state for a number of widget types

	:param settings: settings object to use
	:type settings: QtCore.QSettings
	:param widget: widget to save
	:type widget: QtGui.QWidget
	:param key: (Optional) key to save it as, uses objectName if None
	:type key: str
	:param save: Save if True, Load if False
	:type save: bool
	"""
	isinstance(settings, QtCore.QSettings)
	if not key:
		key = widget.objectName()
		if not key:
			return

	handled = True
	settings.beginGroup('ControlStates')
	try:
		if not save:
			if not settings.contains(key):
				return
			value = settings.value(key)
			if value == 'false':
				value = False
			elif value == 'true':
				value = True

		###Checkable/Check widgets###
		if isinstance(widget, QtGui.QCheckBox):
			if save:
				settings.setValue(key, widget.checkState())
			else:
				widget.setCheckState(int(value))

		elif isinstance(widget, QtGui.QAbstractButton) and widget.isCheckable():
			if save:
				settings.setValue(key, widget.isChecked())
			else:
				widget.setChecked(value)

		elif isinstance(widget, QtGui.QAction) and widget.isCheckable():
			if save:
				settings.setValue(key, widget.isChecked())
			else:
				widget.setChecked(value)

		elif isinstance(widget, QtGui.QGroupBox) and widget.isCheckable():
			if save:
				settings.setValue(key, widget.isChecked())
			else:
				widget.setChecked(value)
				widget.toggled.emit(value)

		###Dropdown/index widgets###
		elif isinstance(widget, QtGui.QComboBox):
			if save:
				settings.setValue(key, widget.currentText())
			else:
				index = widget.findText(value)
				if index >= 0:
					widget.setCurrentIndex(widget.findText(value))

		elif isinstance(widget, QtGui.QTabWidget):
			if save:
				settings.setValue(key, widget.currentIndex())
			else:
				widget.setCurrentIndex(int(value))


		###Text Widgets###
		elif isinstance(widget, QtGui.QLineEdit):
			if save:
				settings.setValue(key, widget.text())
			else:
				widget.setText(value)

		elif isinstance(widget, QtGui.QPlainTextEdit):
			if save:
				settings.setValue(key, widget.toPlainText())
			else:
				widget.setPlainText(value)

		elif isinstance(widget, QtGui.QTextEdit):
			if save:
				settings.setValue(key, widget.toHtml())
			else:
				widget.setHtml(value)

		###List/Tree headers###
		elif isinstance(widget, QtGui.QHeaderView):
			if save:
				indices = range(widget.count())
				for i in range(widget.count()):
					indices[widget.visualIndex(i)] = i
				settings.setValue(key, widget.saveState())
				settings.setValue(key + '_order', indices)
			else:
				order = settings.value(key + '_order')
				widget.restoreState(value)
				indices = [int(v) for v in order]
				for i, logicalIndex in enumerate(indices):
					widget.moveSection(widget.visualIndex(logicalIndex), i)

		###Splitters, sliders, odd widgets###
		elif isinstance(widget, QtGui.QSplitter):
			if save:
				sizes = widget.sizes()
				if sum(sizes):
					settings.setValue(key, sizes)
			else:
				widget.setSizes([float(v) for v in value])

		elif isinstance(widget, QtGui.QAbstractSlider):
			if save:
				settings.setValue(key, widget.sliderPosition())
			else:
				widget.setSliderPosition(float(value))

		elif isinstance(widget, QtGui.QSpinBox) or isinstance(widget, QtGui.QDoubleSpinBox):
			if save:
				settings.setValue(key, widget.value())
			else:
				if isinstance(widget, QtGui.QSpinBox):
					widget.setValue(int(value))
				else:
					widget.setValue(float(value))

		elif isinstance(widget, QtGui.QDateTimeEdit):
			if save:
				settings.setValue(key, widget.dateTime())
			else:
				widget.setDateTime(value)

		elif isinstance(widget, QtGui.QCalendarWidget):
			if save:
				settings.setValue(key, widget.selectedDate())
			else:
				widget.setSelectedDate(value)

		else:
			handled = False
		

		if not handled:
			mode = 'save' if save else 'load'
			log.debug('Unable to %s control, its type is not supported: (%s)%s'%(mode, type(widget), widget))
		else:
			mode = 'Saved' if save else 'Loaded'
			log.debug('%s widget: %s with key: %s'%(mode, widget, key))

	finally:
		settings.endGroup()


###-----------------------------------------------------###
###Maya specific helpers, won't function outside of maya###
###-----------------------------------------------------###
def pathToWidget(mayaName):
	"""
	Given the name of a Maya UI element of any type, return the corresponding QWidget or QAction.
	If the object does not exist, returns None

	:param mayaName: Maya name to get a Qt widget for
	:type mayaName: str
	:return: Widget Object
	:rtype: QtCore.QWidget
	"""
	ptr = omUI.MQtUtil.findControl(mayaName)
	if ptr is None:
		ptr = omUI.MQtUtil.findLayout(mayaName)
		if ptr is None:
			ptr = omUI.MQtUtil.findMenuItem(mayaName)
	return wrapinstance(ptr)


def getMayaWindow():
	"""
	Get the maya main window as a QMainWindow instance

	:return: MainWindow instance
	:rtype: QtGui.QMainWindow
	"""
	try:
		ptr = omUI.MQtUtil.mainWindow()
		return wrapinstance(ptr)
	except Exception:
		return None


def widgetToPath(widget):
	"""
	Return the maya full ui path to the given Qt widget

	:param widget: Qt widget to get a Maya path for if possible
	:type widget: QtGui.QWiget or QtCore.QObject
	:return: Maya UI path, or None
	:rtype: str
	"""
	if widget is None:
		return ''
	return omUI.MQtUtil.fullName(unwrapinstance(widget))


def getParentWidget(widget):
	"""
	Take a given QWidget and return it's Maya UI parent

	:param widget: widget to get parent for
	:type widget: QtGui.QWidget
	:return: Parent widget or None
	:rtype: QtGui.QWidget
	"""
	ptr = omUI.MQtUtil.getParent(unwrapinstance(widget))
	return wrapinstance(long(ptr))


###------------------------------------------------###
###InitialSettings object for resetSettings support###
###------------------------------------------------###
class InitialSettings(dict):
	"""
	A python dictionary with a similar API to QSettings in order to store
	 a backup of the initial form settings when using loadUiFile
	"""

	def __init__(self, *args):
		super(InitialSettings, self).__init__(*args)
		self._group = []

	def getGroupKey(self, key):
		return '/'.join(self._group + [key])

	def setValue(self, key, value):
		self[self.getGroupKey(key)] = value

	def value(self, key, default=None):
		return self.get(self.getGroupKey(key), default)

	def contains(self, key):
		return self.getGroupKey(key) in self

	def beginGroup(self, groupName):
		self._group.append(groupName)

	def endGroup(self):
		self._group.pop(-1)

	def group(self):
		return '/'.join(self._group)



###--------------------------------------------------------------------###
###Callback class to behave like partial but with undo support for PyQt###
###--------------------------------------------------------------------###
if has_maya:
	class BaseCallback(object):
		"""
		Callback object similar to functools.partial.
		It bakes arguments at creation time and makes itself callable.
		"""
		def __init__(self, func, *args, **kwargs):
			#Update the self to match the function signature using functools.update_wrapper
			update_wrapper(self, func)
			self.func = func
			self.args = args
			self.kwargs = kwargs

			#Partial objects dont have a __name__, add it if missing
			if not hasattr(self.func, '__name__'):
				self.func.__name__ = type(self.func).__name__

			#Internal vars, ideally these wont clash with user args...
			self.noUndo = self.kwargs.pop('_callbackNoUndo', False)
			self.useCallArgs = self.kwargs.pop('_callbackWithArgs', False)
			self.callbackName = self.kwargs.pop('_callbackName', self.func.__name__)

		def __str__(self):
			return self.func.__name__

		def __repr__(self):
			return '<<Callback function="%s", Args=%s, Kwargs=%s>>'%(self.func.__name__, self.args, self.kwargs)

		def __get__(self, obj, type=None):
			"""
			Handle class methods as well
			"""
			func = partial(self, obj)
			update_wrapper(func, self.func) #Mask the partial as the original class method
			return func

	if om.MGlobal.apiVersion()>201400: #2014
		#supports the undoChunk argument and handles nested undo chunks better
		class Callback(BaseCallback):
			def __call__(self, *args, **kwargs):
				call_args = self.args[:]
				call_kwargs = self.kwargs.copy()
				if self.useCallArgs:
					call_args+=args
					call_kwargs.update(kwargs)
				name = str(self.callbackName)

				#Prepare undo queue
				if not self.noUndo:
					#Open and close an undo chunk to make sure this gets compressed to a single undo
					cmds.undoInfo(openChunk=True, chunkName=name)
				else:
					#Unless we are in "No Undo" mode, in which case we temporarily disable the undo queue and then restore it's state afterwards
					state = cmds.undoInfo(q=True, st=True)
					cmds.undoInfo(swf=False)

				#Run function
				try:
					log.info('Running Callback(%s): (%s)\n\tArgs: %s\n\tKwargs: %s'%(name, self.func, call_args, call_kwargs))
					return self.func(*call_args, **call_kwargs) #Run Callback

				#Cleanup after function
				finally:
					if not self.noUndo:
						cmds.undoInfo(closeChunk=True)
					else:
						cmds.undoInfo(swf=state)
	else:
		#Must handle undo chunks names the old way, and deal with nested undo chunks...
		#Define Callback function to handle our callback wrapper
		mel.eval("global proc Callback(string $description){};")
		class Callback(BaseCallback):
			@classmethod
			def callbackStack(cls):
				return __main__.__dict__.setdefault('%s.%s_Stack'%(__name__, cls.__name__), [])

			def __call__(self, *args, **kwargs):
				stack = self.callbackStack()
				stack.append(self)
				stack_depth = len(stack)-1
				try:
					call_args = self.args[:]
					call_kwargs = self.kwargs.copy()
					if self.useCallArgs:
						call_args+=args
						call_kwargs.update(kwargs)
					name = str(self.callbackName)

					#Prepare undo queue
					if not self.noUndo:
						#Open and close an undo chunk to make sure this gets compressed to a single undo
						if not stack_depth:
							cmds.undoInfo(openChunk=True)
							try:
								mel.eval('Callback "%s"'%name)
							except (SyntaxError, ValueError):
								pass
					else:
						#Unless we are in "No Undo" mode, in which case we temporarily disable the undo queue and then restore it's state afterwards
						state = cmds.undoInfo(q=True, st=True)
						cmds.undoInfo(swf=False)

					#Run function
					try:
						log.info('Running Callback(%s): %s (%s)\n\tArgs: %s\n\tKwargs: %s'%(name, stack_depth, self.func, call_args, call_kwargs))
						return self.func(*call_args, **call_kwargs) #Run Callback

					#Cleanup after function
					finally:

						if not self.noUndo:
							if not stack_depth:
								cmds.undoInfo(closeChunk=True)
						else:
							cmds.undoInfo(swf=state)

				finally:
					stack.pop(-1)
else:
	Callback = partial


def undoable(func):
	"""
	Make the decorated function undoable in Maya using a Callback

	:param func: function to decorate
	:type func: callable
	:return: Wrapper Callback
	:rtype: Callback
	"""
	if globals().has_key('maya'):
		callback = Callback(func, _callbackWithArgs=True)
		return callback
	else:
		return func

def notundoable(func):
	"""
	Make the decorated function not undoable in Maya using a Callback

	:param func: Decorated function
	:type func: callable
	:return: Wrapper Callback
	:rtype: Callback
	"""
	if globals().has_key('maya'):
		callback = Callback(func, _callbackWithArgs=True, _callbackNoUndo=True)
		return callback
	else:
		return func

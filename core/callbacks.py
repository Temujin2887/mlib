__author__ = 'Nathan'
__doc__ =\
"""
Callbacks system

Events are registered "as needed"


Basic example
--------------

import mlib.core.callbacks as callbacks
reload(callbacks)
print '\n'.join(callbacks.getEvents())


def test():
	print 'YAY!'

callbacks.addCallback('SelectionChanged', 'test', test)
callbacks.removeCallback('SelectionChanged', 'test')

rfunc, dfunc = make_user_event_funcs('myEvent')
callbacks.addEvent('myEvent', rfunc, dfunc)

callbacks.addCallback('myEvent', 'test', test)
callbacks.postEvent('myEvent')



"""

import __main__
import logging
import collections
from functools import partial


import maya.cmds as cmds
import maya.OpenMaya as om

log = logging.getLogger(__name__)

#Load in the globals
callbacks = __main__.__dict__.setdefault(__name__+'.registered_callbacks', {})
events = __main__.__dict__.setdefault(__name__+'.supported_events', {})
event_handles = __main__.__dict__.setdefault(__name__+'.event_handles', {})
event_queue = __main__.__dict__.setdefault(__name__+'.event_queue', {})

Callback = collections.namedtuple('Callback', ['event', 'owner', 'function', 'priority', 'immediate'])
Event = collections.namedtuple('Event', ['name', 'register_func', 'deregister_func', 'disable_undo', 'allow_deferred', 'deferred_low_priority', 'builtin'])

def getEvents():
	return sorted(events.keys())

def addCallback(event, owner, function, priority=None, immediate=None):
	callback = Callback(event, owner, function, priority, immediate)

	#Check if event is registered
	if not event in event_handles:
		_registerEvent(event)

	callbacks.setdefault(event, {})[owner] = callback

def removeCallback(event, owner):
	event_callbacks = callbacks.get(event, [])
	if owner in event_callbacks:
		event_callbacks.pop(owner)

		#Clean up unused event
		if not event_callbacks:
			_deregisterEvent(event)

		return True
	return False

def getCallbacks(event=None):
	"""
	Returns a list of all callbacks, sorted by priority

	:param event: (Optional) event name to filter to
	:type event: str or None
	:return: callbacks
	:rtype: list
	"""
	#Sorter
	priority_sort = lambda callback: (callback.event.lower(),
	                                 callback.priority,
	                                 callback.immediate,
									 callback.owner,)
	if event is not None:
		return sorted(callbacks.get(event, {}).values(), key=priority_sort, reverse=True)
	return sorted(sum(callbacks.values()), key=priority_sort, reverse=True)


def postEvent(event, *args, **kwargs):
	print 'Post!'
	if om.MUserEventMessage.isUserEvent(event):
		print 'Post user event!'
		om.MUserEventMessage.postUserEvent(event, *args, **kwargs)
	else:
		event_handler(event, *args, **kwargs)

def addEvent(event, register_func, deregister_func, disable_undo=False, allow_deferred=False, deferred_low_priority=False, builtin=False):
	if event in getEvents() and not builtin:
		raise ValueError('Duplicate event name!')
	events[event] = Event(event, register_func, deregister_func, disable_undo, allow_deferred, deferred_low_priority, builtin)

def event_handler(event, *args, **kwargs):
	"""

	:param event:
	:param args:
	:param kwargs:
	:return:
	"""
	print 'Event Handler!', event
	if event not in events:
		log.error('Event handler called for event that is not supported! "%s"'%event)
		return

	checkFile = ('checkFile' in kwargs)
	if checkFile: #Dont block file open checks
		retCode = args[0]
		mFile = args[1]
		om.MScriptUtil.setBool(retCode, True)

	event_callbacks = getCallbacks(event)
	allow_deferred = events[event].allow_deferred
	immediate_callbacks = [callback for callback in event_callbacks if callback.immediate or not allow_deferred]
	if immediate_callbacks:
		log.debug('Event %s Callbacks: %s'%(event, immediate_callbacks))

	add_to_queue = len(immediate_callbacks)<event_callbacks
	for callback in immediate_callbacks:
		try:
			if checkFile:
				callback.function(mFile, retCode, *[arg for arg in args[2:] if arg is not None])
			elif len([v for v in args if v is not None]):
				callback.function(*args)
			else:
				callback.function()
		except:
			log.exception('Error handling event "%s" with event handler "%s"\n'%(event, callback.owner))

	if add_to_queue:
		if not event_queue.get(event):
			event_queue[event] = True
			cmds.evalDeferred(partial(queued_event_handler, event, *args, **kwargs),
			                  lowestPriority=events[event].deferred_low_priority)

def queued_event_handler(event, *args, **kwargs):
	event_callbacks = getCallbacks(event)
	deferred_callbacks = [callback for callback in event_callbacks if not callback.immediate]
	log.debug('Queued event "%s" Callbacks: %s'%(event, deferred_callbacks))

	for callback in deferred_callbacks:
		if not callback.immediate:
			try:
				if len([v for v in args if v is not None]):
					callback.function(*args)
				else:
					callback.function()
			except:
				log.exception('Error handling queued event "%s" with event handler "%s"\n'%(event, callback.owner))

	#Allow another event to queue
	event_queue[event] = False


def _registerEvent(event):
	if not event in events:
		raise ValueError('Invalid event name: %s, not in supported events list!'%event)

	if event in event_handles:
		if not _deregisterEvent(event):
			raise SystemError('Could not de-register old event handler, unable to re-register event: "%s"'%event)

	event_handles[event] = events[event].register_func()
	return True

def _deregisterEvent(event):
	if not event in events:
		raise ValueError('Invalid event name: %s, not in supported events list!'%event)

	if not event in event_handles:
		return True

	handle = event_handles[event]
	try:
		if handle is not None:
			events[event].deregister_func(handle)
		else:
			events[event].deregister_func()
		del event_handles[event]
		return True
	except:
		log.exception('Error deregistering event "%s":\n'%event)
		return False

def make_user_event_funcs(event):
	"""

	:param event:
	:return:
	"""
	def rfunc(event):
		om.MUserEventMessage.registerUserEvent(event)
		om.MUserEventMessage.addUserEventCallback(event, partial(event_handler, event))

	def dfunc(event, id):
		om.MMessage.removeCallback(id)
		om.MUserEventMessage.deregisterUserEvent(event)

	return partial(rfunc, event), partial(dfunc, event)

def add_default_events():
	_temp = []
	#Add builtin events
	om.MEventMessage.getEventNames(_temp)
	for mevent in sorted(_temp):
		rfunc = partial(om.MEventMessage.addEventCallback, mevent, partial(event_handler, mevent))
		dfunc = om.MMessage.removeCallback

		addEvent(mevent, rfunc, dfunc, disable_undo=False, allow_deferred=True, builtin=True)

	#Add scene events
	scene_events = [
		'AfterSave', 'BeforeSave',
		'BeforeOpen', 'AfterOpen',
		'BeforeImport', 'AfterImport',
		'BeforeLoadReference', 'AfterLoadReference',
		'BeforeLoadReferenceAndRecordEdits', 'AfterLoadReferenceAndRecordEdits',
		'BeforeUnloadReference', 'AfterUnloadReference',
		'BeforeRemoveReference', 'AfterRemoveReference',
		'BeforeCreateReference', 'AfterCreateReference',
		'BeforeCreateReferenceAndRecordEdits', 'AfterCreateReferenceAndRecordEdits',
		'BeforeNew', 'AfterNew',
		'SceneUpdate',
		'MayaExiting',
	]

	for mevent in scene_events:
		event_id = getattr(om.MSceneMessage, 'k%s'%mevent)

		rfunc = partial(om.MSceneMessage.addCallback, event_id, partial(event_handler, mevent))
		dfunc = om.MMessage.removeCallback
		disable_undo = mevent in ['Undo', 'Redo']

		addEvent(mevent, rfunc, dfunc, disable_undo=disable_undo, allow_deferred=True, builtin=True)


	#Add scene check events
	scene_check_events = [
		('BeforeNewCheck', False),
		('BeforeOpenCheck', True),
	    ('BeforeSaveCheck', False),
	    ('BeforeImportCheck', True),
	    ('BeforeExportCheck', True),
	    ('BeforeReferenceCheck', False),
	    ('BeforeLoadReferenceCheck', True),
	    ('BeforeCreateReferenceCheck', True),
	]

	for mevent, checkFile in scene_check_events:
		event_id = getattr(om.MSceneMessage, 'k%s'%mevent)

		if checkFile:
			rfunc = partial(om.MSceneMessage.addCheckFileCallback, event_id, partial(event_handler, mevent, checkFile=True))
		else:
			rfunc = partial(om.MSceneMessage.addCheckCallback, event_id, partial(event_handler, mevent))
		dfunc = om.MMessage.removeCallback

		addEvent(mevent, rfunc, dfunc, disable_undo=False, allow_deferred=False, builtin=True)

add_default_events()
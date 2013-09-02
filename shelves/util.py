__author__ = 'Nathan'

import os
import json
import logging
import __main__

from ..lib import misc

import maya.cmds as cmds

log = logging.getLogger(__name__)

class ShelfManager(object):
	@classmethod
	def get(cls, refresh=False):
		iname = __name__+'.'+cls.__name__+'.instance%s'
		if not iname in __main__.__dict__ or refresh:
			__main__.__dict__[iname] = cls()
		return __main__.__dict__[iname]

	def __init__(self):
		paths = [os.path.join(cmds.internalVar(upd=True), 'shelf2')]
		self.shelves = self.parseJSON(paths, 'shelf')
		self.items = self.parseJSON(paths, 'item')
		self.commands = self.parseJSON(paths, 'commands')

	def saveAll(self):
		for item in self.shelves+self.items+self.commands:
			if not 'path' in item:
				log.error('No path for item, unable to save: %s'%item)
				continue

			try:
				with open(item['path'], 'w') as f:
					json.dump(item, f)
			except (ValueError, OSError):
				log.exception('Failed to save shelf item to disk:\n')

	@staticmethod
	def parseJSON(paths, extension):
		parsed = []
		for path in paths:
			path = os.path.normpath(path)
			for root, folder, files in os.walk(path):
				validFiles = [os.path.join(root, f) for f in files if f.endswith('.%s'%extension)]
				for validFile in validFiles:
					with open(validFile, 'r') as f:
						try:
							data = json.load(f)
							data['path'] = validFile
							parsed.append(data)
						except ValueError:
							log.exception('Failed to read shelf file "%s", json Exception:\n'%validFile)
							continue
		return parsed


def validateGuids(items):
	seen = set()
	for item in items:
		guid = item.get('guid')
		if not guid:
			item['guid'] = misc.generateGuid()
	return items


#JSON Templates
shelf = {
	'guid':None,
	'name':'New Shelf',
    'tooltip':'',
    'items':[],
    'icon':None,
    'slot_initialize':None,
}

item = {
	'guid':None,
    'name':'New Item',
    'tooltip':'',
    'label':{},
	'icon':None,
    'mode':'button',
    'update_events':[],
    'slot_context_menu':None,
    'slot_action':None,
    'slot_popup':None,
    'slot_update':None,
}

command = {
	'guid':None,
    'command':'',
    'name':'Command',
    'description':'',
}
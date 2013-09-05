__author__ = 'Danny Wynne'

import logging
import __main__

from ..core import qt
from . import main

reload(main)

log = logging.getLogger(__name__)

def install_channel_box():
	win = qt.getMayaWindow()
	try:
		box = __main__.__dict__[__name__+'_channel_box']
		win.removeDockWidget (box)
	except KeyError:
		pass

	channel_box = shelfbar.ShelfBar(qt.getMayaWindow())
	win.addDockWidget(channel_box)
	__main__.__dict__[__name__+'_channel_box'] = channel_box

'''
import mlib.shelves
reload(mlib.shelves)
mlib.shelves.install_toolbar()
'''
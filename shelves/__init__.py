__author__ = 'Nathan'

import logging
import __main__

from ..core import qt
from . import shelfbar

log = logging.getLogger(__name__)

def install_toolbar():
	win = qt.getMayaWindow()
	try:
		bar = __main__.__dict__[__name__+'_toolbar']
		win.removeToolBar(bar)
	except KeyError:
		pass

	toolbar = shelfbar.ShelfBar(qt.getMayaWindow())
	win.addToolBar(toolbar)
	__main__.__dict__[__name__+'_toolbar'] = toolbar

'''
import mlib.shelves
reload(mlib.shelves)
mlib.shelves.install_toolbar()
'''
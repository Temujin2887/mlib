import os
import sys
import shutil
from sphinx import cmdline

build_dir = os.path.abspath(sys.argv[-1])

for path in os.listdir(build_dir):
	fpath = os.path.join(build_dir, path)
	if os.path.isdir(fpath) and path not in ['.git']:
		print 'Nuke dir:', path
		shutil.rmtree(fpath)
	elif not path.startswith('.'):
		print 'Nuke file:', path
		os.remove(fpath)


cmdline.main(sys.argv)

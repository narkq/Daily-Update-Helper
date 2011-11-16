#!/usr/bin/python
# -*- coding: utf-8
# vim:fileencoding=utf-8
import os, sys, shutil

cfg_dir_path = '~/.duh'
cfg_path = cfg_dir_path + '/config'
todo_path = cfg_dir_path + '/todo'

cfg_dir_real_path = os.path.normpath(os.path.expanduser(cfg_dir_path))
cfg_real_path = os.path.normpath(os.path.expanduser(cfg_path))
todo_real_path = os.path.normpath(os.path.expanduser(todo_path))

try:
	if not os.path.isdir(cfg_dir_real_path):
		print 'Creating config dir...'
		os.mkdir(cfg_dir_real_path, 0700)
except IOError:
	print 'Could not create my config dir'
	exit()

filename = '/config.default.' + sys.platform
filename = os.path.abspath(os.path.dirname(__file__) + filename)
try:
	shutil.copyfile(filename, cfg_real_path)
except IOError as error:
	print 'Could not copy default config file to "', cfg_dir_real_path, '" (', error, ')'

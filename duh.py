#!/usr/bin/python
# -*- coding: utf-8
# vim:fileencoding=utf-8
import os
import re, string
import getpass
import ConfigParser
import xmlrpclib
from datetime import date

def ensure_cfg_param(cfg, cfg_path, section, param, do_input=raw_input):
	cfg_need_update = False
	if not cfg.has_section(section):
		cfg.add_section(section)
	if cfg.has_option(section, param):
		value = cfg.get(section, param)
	else:
		value = do_input('"' + section + '.' + param + '" option not set. Please specify it here: ')
		cfg_need_update = True
	while not value:
		value = do_input('Specified "' + section + '.' + param + '" option value is empty. Please enter non-empty value: ')
		cfg_need_update = True
	cfg.set(section, param, string.replace(value, '%', '%%'))
	if cfg_need_update:
		cfg_fp = open(cfg_real_path, 'w')
		cfg.write(cfg_fp)
		cfg_fp.close()
	value = value.decode('utf-8')
	return value

def ensure_valid_regex(regex_src):
	try:
		regex = re.compile(regex_src, re.U)
	except:
		print 'Invalid regex /', regex_src, '/'
		exit()
	return regex

if os.system('git status -s -uno'):
	print 'Please run this script from a git repository.'
	exit()

cfg = ConfigParser.SafeConfigParser()

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

try:
	cfg_fp = open(cfg_real_path, 'r')
	cfg.readfp(cfg_fp)
	cfg_fp.close()
except IOError:
	cfg_fp = open(cfg_real_path, 'w')
	cfg_fp.write('')
	cfg_fp.close()

uri = ensure_cfg_param(cfg, cfg_real_path, 'wiki', 'uri')
login = ensure_cfg_param(cfg, cfg_real_path, 'wiki', 'login')
password = ensure_cfg_param(cfg, cfg_real_path, 'wiki', 'password', getpass.getpass)
space_name = ensure_cfg_param(cfg, cfg_real_path, 'wiki', 'space')
page_name_tpl = ensure_cfg_param(cfg, cfg_real_path, 'wiki', 'page')

page_name = date.today().strftime(page_name_tpl);

token = False
try:
	proxy = xmlrpclib.ServerProxy(uri)
	token = proxy.confluence1.login(login, password)
except xmlrpclib.Fault as error:
	print 'Could not log in as ', login, ' at ', uri, ': ', error
except (IOError, xmlrpclib.ProtocolError) as error:
	print 'Could not contact ', uri, ': ', error
if not token:
	exit()

page = False
try:
	page = proxy.confluence1.getPage(token, space_name, page_name)
except xmlrpclib.Fault as error:
	print 'Could not retrieve page "' + space_name + '.' + page_name + '": ', error
finally:
	proxy.confluence1.logout(token)
if not page:
	exit()

# get branch names
lines = page['content'].splitlines(True)

branch_name_regex = ensure_cfg_param(cfg, cfg_real_path, 'general', 'branch_name_regex')
branch_name_finder = ensure_valid_regex(branch_name_regex)
branch_start_regex = ensure_cfg_param(cfg, cfg_real_path, 'general', 'branch_start_regex')
branch_start_finder = ensure_valid_regex(branch_start_regex)
branch_stop_regex = ensure_cfg_param(cfg, cfg_real_path, 'general', 'branch_stop_regex')
branch_stop_finder = ensure_valid_regex(branch_stop_regex)

branches = ['lol\n']
start_flag = False
for line in lines:
	if branch_stop_finder.search(line):
		break
	if not start_flag:
		if branch_start_finder.search(line):
			start_flag = True
	if start_flag:
		match = branch_name_finder.search(line)
		if match:
			branch_name = match.group(1)
			if branch_name:
				branches.append(branch_name + "\n")
				#todo_fd.write(branch_name + "\n")

if not len(branches):
	print 'Nothing to do.'
	exit()

todo_fd = open(todo_real_path, 'w')
todo_fd.writelines(branches)
todo_fd.close()

editor = ensure_cfg_param(cfg, cfg_real_path, 'general', 'editor')
if os.system(editor + ' ' + todo_real_path):
	print 'Editing todo failed!'
	exit()

todo_fd = open(todo_real_path, 'r')
branches = []
for line in todo_fd:
	branches.append(line.rstrip())
todo_fd.close()
os.unlink(todo_real_path)

if not len(branches):
	print 'Nothing to do.'
	exit()

base_branch = ensure_cfg_param(cfg, cfg_real_path, 'git', 'base_branch');
tmp_branch_prefix = ensure_cfg_param(cfg, cfg_real_path, 'git', 'tmp_branch_prefix');
rebase_flags = ensure_cfg_param(cfg, cfg_real_path, 'git', 'rebase_flags');
merge_flags = ensure_cfg_param(cfg, cfg_real_path, 'git', 'merge_flags');
checkout_flags = ensure_cfg_param(cfg, cfg_real_path, 'git', 'checkout_flags');

os.system('git fetch --all')

results = {}

for branch in branches:
	tmp_branch = tmp_branch_prefix + branch
	results[branch] = {'status': 'success', 'color': 'green', 'reason': ''}
	if os.system('git checkout ' + checkout_flags + ' ' + branch):
		results[branch] = {'status': 'failure', 'color': 'red', 'reason': 'initial checkout failed'}
		continue
	if os.system('git checkout -b ' + tmp_branch):
		results[branch] = {'status': 'warning', 'color': 'green', 'reason': 'temporary branch overwritten'}
		os.system('git checkout ' + checkout_flags + ' ' + tmp_branch)
		os.system('git reset --hard ' + tmp_branch)
	if os.system('git rebase ' + rebase_flags + ' ' + base_branch):
		results[branch] = {'status': 'failure', 'color': 'red', 'reason': 'rebase failed'}
		os.system('git rebase --abort')
		os.system('git checkout ' + checkout_flags + ' ' + base_branch)
		os.system('git branch -D ' + tmp_branch)
		continue
	os.system('git checkout ' + checkout_flags + ' ' + base_branch)
	os.system('git merge ' + merge_flags + ' ' + tmp_branch)
	os.system('git branch -D ' + tmp_branch)

print '\n\n\n'
print '                                  === SUMMARY ===                                 '
print '----------------------------------------------------------------------------------'
print '{b:20}\t{s:7}\t{r}'.format(b='branch', s='status', r='reason')
print '----------------------------------------------------------------------------------'

for branch in branches:
	print '{b:20}\t{s:7}\t{r}'.format(b=branch, s=results[branch]['status'], r=results[branch]['reason'])

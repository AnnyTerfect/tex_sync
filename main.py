#-*- coding: utf-8 -*-
from mywatcher import MyWatcher, MyHandler
from urltracker import URLTracker
from os import chdir
from fire import Fire

def main(url='', email='', password='', work_dir='.'):
	chdir(work_dir)
	watcher = MyWatcher()
	tracker = URLTracker(watcher)
	handler = MyHandler(tracker.wd)
	watcher.set_handler(handler)

	#auto login
	if url:
		tracker.wd.get(url)
		if email and password:
			tracker.login(email, password)
			
	tracker.start()

if __name__ == '__main__':
	Fire(main)
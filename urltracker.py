#-*- coding: utf-8 -*-
from pickle import dump, load
from os.path import exists
from selenium.webdriver import Chrome
from time import sleep
from logger import logger
from threading import Thread

class URLTracker:
	def __init__(self, watcher):
		self.wd = Chrome()
		self.watcher = watcher
		#self.load_cookie()

	def load_cookie(self):
		if exists('cookies'):
			with open('cookies', 'rb') as rf:
				self.cookies = load(rf)
				cookies = self.cookies
				for cookie in cookies:
					self.wd.add_cookie(cookie)
				logger.info('Cookies load successfully.')

	def dump_cookie(self):
		self.cookies = self.wd.get_cookies()
		with open('cookies', 'wb') as wf:
			dump(self.cookies, wf)

	def login(self, email, password):
		wd = self.wd
		wd.find_element_by_name('email').send_keys(email)
		wd.find_element_by_name('password').send_keys(password)
		wd.find_elements_by_xpath('//button[@type = "submit"]')[0].click()

	def close_window(self):
		def target(wd):
			while True:
				ele = wd.find_elements_by_xpath('//button[@ng-click = "done()"]')
				if len(ele):
					ele[0].click()
				sleep(3)
		th = Thread(target=target, args=(self.wd,))
		#th.start()

	def start(self):
		wd = self.wd
		watcher = self.watcher
		while True:
			url = wd.current_url
			url_parts = url.split('/')

			if url_parts[-1] == 'project':
				#self.dump_cookie()

				logger.info('Waiting for entering a project')
				#wait for url change
				while True:
					if wd.current_url != url:
						sleep(0.1)
						break
					#do nothing

			if len(url_parts) >= 2 and url_parts[-2] == 'project':
				logger.info('A project found, start syncing.')
				self.close_window()
				#start watching
				watcher.start()

				#wait for url change
				while True:
					if wd.current_url != url:
						watcher.stop()
						sleep(0.1)
						break

			sleep(0.1)
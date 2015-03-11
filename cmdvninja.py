import sublime, sublime_plugin
import requests
import urllib
import json

import webbrowser # Need to implement a feature to open our webpage in the default browser

# Not sure what I really need here, pulled from Gist plug in
# import os
# import os.path
# import sys
# import functools
# import tempfile
# import traceback
# import threading
# import shutil

class ExampleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.window().show_input_panel("Input:", "", self.done, None, None)

	def done(self, value):
		data = urllib.quote(value)
		print data

# Currently returns a list of all of your snippets
class MysnippetsCommand(sublime_plugin.TextCommand):
	# Might need to pass a header in this command
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.cmdv_ninja = self.settings.get("accounts").get("cmdv_ninja")
		self.token = self.cmdv_ninja.get("token")
		# self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			self.view.window().show_input_panel("Token:", "", self.set_token, None, None) 
		else: 
			self.snippet_menu()

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.snippet_menu()

	def snippet_menu(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://localhost:3000/api/users/{0}/snippets'.format(self.token)).json()
		for snippet in self.snippet_collection:
			snippet_titles.append(snippet['unique_handle'])
		self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))


# Returns a menu of all a users snippets 
class MycollectionsCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.accounts = self.settings.get("accounts")
		self.cmdv_ninja = self.accounts.get("cmdv_ninja")
		# self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		self.token = self.cmdv_ninja.get("token")
		# self.url = self.cmdv_ninja.get("base_uri")
		self.groups = []
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			self.view.window().show_input_panel("Token:", "", self.set_token, None, None) 
		else: 
			self.get_collections()

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_collections()

	def get_collections(self):
		group_titles = []
		print 'fetching groups'
		self.groups = requests.get('http://localhost:3000/api/users/{0}/groups'.format(self.token)).json()
		for group in self.groups:
			group_titles.append(group['name'])
		self.view.window().show_quick_panel(group_titles, self.select_group)

	def select_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://localhost:3000/api/groups/{0}/snippets'.format(self.group['_id'])).json()
		for snippet in self.snippet_collection:
			snippet_titles.append(snippet['unique_handle'])
		self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			print self.snippet['unique_handle']
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))


# Creates a new snippet on the database from the clipboard
# Have Gary create a new 
class CreatesnipCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.edit = edit # Not sure I'll need this
		self.token = sublime.load_settings('cmdvninja.sublime-settings').get("accounts").get("cmdv_ninja").get("token")
		self.new_snippet = sublime.get_clipboard().encode('utf-8')
		# Need token auth here too
		self.get_unique_handle()

	def get_unique_handle(self):
		self.view.window().show_input_panel("Title:", "", self.set_unique_handle, None, None)

	def set_unique_handle(self, value):
		self.unique_handle = value
		self.create_new_snippet()

	def create_new_snippet(self):
		new_snippet = {"user": self.token, "content": self.new_snippet, "unique_handle": self.unique_handle}
		response = requests.post('http://localhost:3000/api/groups/{0}/snippets', data=new_snippet ) # Change this route 
		if response.status_code == 200: 
			sublime.message_dialog("{0} successfully saved to CmdV Ninja!".format(self.unique_handle))
		else:
			sublime.error_message("Snippet failed to save. Please check internet connection or try a different title.")


# Currently searches all snippets and allows for cyclical searching until an element is selected 
class SearchCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.cmdv_ninja = self.settings.get("accounts").get("cmdv_ninja")
		# self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		self.token = self.cmdv_ninja.get("token")
		self.url = self.cmdv_ninja.get("base_uri")
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			self.view.window().show_input_panel("Token:", "", self.set_token, None, None) 
		else: 
			self.get_search()

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_search()

	def get_search(self):
		self.view.window().show_input_panel("Snippet", "", self.show_menu, self.fuzzy_search, None)

	def fuzzy_search(self, value):
		self.snippet_titles = []
		self.snippet_collection = requests.get('http://localhost:3000/api/search?type=subl&limit=100&query={0}'.format(urllib.quote(value))).json()
		for snippet in self.snippet_collection:
			self.snippet_titles.append(snippet['unique_handle'])
		self.view.window().show_input_panel("Snippet", value, self.fuzzy_search, None, None)
		self.view.window().show_quick_panel(self.snippet_titles, self.copy_to_clipboard)

	def show_menu(self, value):
		self.view.window().show_quick_panel(self.snippet_titles, self.copy_to_clipboard)

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))


import sublime, sublime_plugin
import requests
import urllib

# Not sure what I really need here, pulled from Gist plug in
import os
import os.path
import sys
import json
import functools
import webbrowser
import tempfile
import traceback
import threading
import shutil

TEST_API = r"http://localhost:3000/users"

STUFF = "Hello, World!"

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
		# self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		self.token = self.cmdv_ninja.get("token")
		self.url = self.cmdv_ninja.get("base_uri")
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			self.view.window().show_input_panel("Username:", "", self.set_username, None, None) 
		else: 
			self.snippet_menu()

	def set_username(self, value):
		self.username = value
		self.get_password()

	def get_password(self):
		self.view.window().show_input_panel("Password:", "", self.log_token, None, None)

	def log_token(self, value):
 		# This is doing an API call that verifies that accuracy of the username
 		self.password = value
 		auth = {'username': self.username, 'password': self.password}
 		user_token = requests.get('http://localhost:3000/api/auth', data=auth)
 		if user_token.status_code == 200:
			self.settings.set("accounts", {"cmdv_ninja": { "token": user_token['id'], "base_uri": "http://localhost:3000/"}})
			sublime.save_settings('cmdvninja.sublime-settings')
			token_json = user_token.json()
			self.token = token_json['id'] # Try combinding this with the line above later
			self.snippet_menu()
		else:
			sublime.error_message("Incorrect username or password")

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
		self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		# self.token = self.cmdv_ninja.get("token")
		self.url = self.cmdv_ninja.get("base_uri")
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			self.view.window().show_input_panel("Username:", "", self.set_username, None, None) 
		else: 
			self.get_collection()

	def set_username(self, value):
		self.username = value
		self.get_password()

	def get_password(self):
		self.view.window().show_input_panel("Password:", "", self.log_token, None, None)

	def log_token(self, value):
 		# This is doing an API call that verifies that accuracy of the username
 		self.password = value
 		auth = {'username': self.username, 'password': self.password}
 		user_token = requests.get('http://localhost:3000/api/auth', data=auth)
 		if user_token.status_code == 200:
			self.settings.set("accounts", {"CodeBag": { "token": user_token['id'], "base_uri": "http://localhost:3000/"}})
			sublime.save_settings('codebag.sublime-settings')
			token_json = user_token.json()
			self.token = token_json['id'] # Try combinding this with the line above later
			self.get_collection()
		else:
			sublime.error_message("Incorrect username or password")


	def get_collection(self):
		self.view.window().show_input_panel("Password:", "", self.return_collection, None, None)

	def set_collection(self, value):
		self.collection = value
		return_collection()

	def return_collection(self):
		print "return collection"
		snippet_titles = []
		self.snippet_collection = requests.get('http://localhost:3000/api/users/{0}/collections/{1}/snippets'.format(self.token, self.collection)).json()
		for snippet in self.snippet_collection:
			snippet_titles.append(snippet['unique_handle'])
		self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			print self.snippet['unique_handle']
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))
		else:
			error_message("Failed to copy snippet to the clipboard")


# Creates a new snippet on the database from the 
class CreatesnipCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.edit = edit # Not sure I'll need this
		self.token = sublime.load_settings('cmdvninja.sublime-settings').get("accounts").get("cmdv_ninja").get("token")
		self.new_snippet = sublime.get_clipboard().encode('utf-8')
		self.get_unique_handle()

	def get_unique_handle(self):
		self.view.window().show_input_panel("Title:", "", self.set_unique_handle, None, None)

	def set_unique_handle(self, value):
		self.unique_handle = value
		self.create_new_snippet()

	def create_new_snippet(self):
		new_snippet = {"user": self.token, "content": self.new_snippet, "unique_handle": self.unique_handle}
		response = requests.post('http://localhost:3000/api/snippets', data=new_snippet )
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
			self.view.window().show_input_panel("Username:", "", self.set_username, None, None) 
		else: 
			self.get_search()

	def set_username(self, value):
		self.username = value
		self.get_password()

	def get_password(self):
		self.view.window().show_input_panel("Password:", "", self.log_token, None, None)

	def log_token(self, value):
 		# This is doing an API call that verifies that accuracy of the username
 		self.password = value
 		auth = {'username': self.username, 'password': self.password}
 		user_token = requests.get('http://localhost:3000/api/auth', data=auth)
 		if user_token.status_code == 200:
			self.settings.set("accounts", {"cmdv_ninja": { "token": user_token['id'], "base_uri": "http://localhost:3000/"}})
			sublime.save_settings('cmdvninja.sublime-settings')
			token_json = user_token.json()
			self.token = token_json['id'] # Try combinding this with the line above later
			self.get_search()
		else:
			sublime.error_message("Incorrect username or password")

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


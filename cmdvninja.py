import sublime, sublime_plugin
import requests

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
import subprocess

TEST_API = r"http://localhost:3000/users"

STUFF = "Hello, World!"

class AuthCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.username = ""
		self.password = ""
		self.get_username()

	def get_username(self):
		self.window.show_input_panel("Username:", "", self.set_username, None, None)

	def set_username(self, value):
		self.username = value
		self.get_password()

	def get_password(self):
		self.window.show_input_panel("Password:", "", self.set_password, None, None)

	def set_password(self, value):
		self.password = value
		self.log_token()

	def log_token(self):
 		# This is doing an API call that verifies that accuracy of the username
 		auth = json.dumps({'username': self.username, 'password': self.password})
 		user_token = requests.get('http://localhost:3000/api/auth', data=auth)
 		if user_token.status_code == 200:
			self.cmdv_ninja.set({ "token": user_token['id'], "base_uri": "http://localhost:3000/"}) # Not sure this will work since it's not self.settings, but let's see
			sublime.save_settings('cmdvninja.sublime-settings')
			token_json = user_token.json()
			self.token = token_json['id'] # Try combinding this with the line above later
			self.token = "working"
			return self.token
		else:
			sublime.error_message("Incorrect username or password")
			return None
		print 'Auth Command Complete'

class ExampleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.window = self.view.window()
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.cmdv_ninja = self.settings.get("accounts").get("cmdv_ninja")
		# self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		self.token = self.cmdv_ninja.get("token")
		self.token = ""
		self.url = self.cmdv_ninja.get("base_uri")
		if self.token == "":
			sublime.set_timeout(self.window.run_command('auth'),50)
			self.complete()
		else:
			print "Has token already"

	def complete(self):
		print 'Example Command Complete'


class ShowCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		self.json_obj = {}
		self.edit = edit
		self.view.window().show_input_panel("Input User:", "users", self.on_done, None, None)

	def on_done(self, value):
		self.json_obj = requests.get(TEST_API).json()
		print self.json_obj
		self.put_to_screen()

	def put_to_screen(self):
		self.view.insert(self.edit, 0, "{0} \n\n".format(self.json_obj['saying']))
		# Leave this for now because this syntax will add the imported code and create two lines of seperation for each one received
		# Ideally this will append to at the end of your code
		# Probably won't need this in favor of copying to clipboard


# Will need to pass header of sublime text

class MysnippetsCommand(sublime_plugin.TextCommand):
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

# class MenuCommand(sublime_plugin.TextCommand):
# 	def run(self, edit):
# 		array = ['stuff', 'things', 'other']
# 		self.view.window().show_quick_panel(array, self.on_done)

# 	def on_done(self, value):
# 		print value

class MycollectionsCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.accounts = self.settings.get("accounts")
		self.cmdv_ninja = self.accounts.get("cmdv_ninja")
		self.token = "54f9e8e2e537f8cc40e63265" # Reserved to test if the primary user
		# self.token = self.codebag.get("token")
		self.url = self.codebag.get("base_uri")
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
		new_snippet = json.dumps({"user": self.token, "content": self.new_snippet, "unique_handle": self.unique_handle})
		response = requests.post('http://localhost:3000/api/users/{0}/snippets', new_snippet )
		print response.status_code # Use this code to set the below if statement, then remove this line
		if response.status_code > 200 and response.status_code < 210: # Make this less hacky at some point
			print 'cool'
			sublime.message_dialog("{0} successfully saved to CmdV Ninja!".format(self.unique_handle))
		else:
			sublime.error_message("Snippet failed to save. Please check internet connection or try a different title.")


import sublime, sublime_plugin
import requests
import urllib
import json
import webbrowser

class AuthCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None)

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		return self.token

##################################################################################################

class OpenappCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		webbrowser.open_new_tab('https://cmdvninja.herokuapp.com/')

##################################################################################################

# Returns a menu of all a users snippets for the selected group
class MygroupsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.accounts = self.settings.get("accounts")
		self.cmdv_ninja = self.accounts.get("cmdv_ninja")
		self.token = self.cmdv_ninja.get("token")
		self.groups = []
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			# self.token = sublime.run_command('auth') # Really want to get this working
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.get_collections()

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_collections()

	def get_collections(self):
		group_titles = []
		self.groups = requests.get('https://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
		for group in self.groups:
			group_titles.append(group['name'])
		self.view.window().show_quick_panel(group_titles, self.select_group)

	def select_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('https://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['_id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################

# Creates a new snippet on the database from the clipboard
class CreatesnipCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.edit = edit # Not sure I'll need this
		self.token = sublime.load_settings('cmdvninja.sublime-settings').get("accounts").get("cmdv_ninja").get("token")
		self.new_snippet = sublime.get_clipboard().encode('utf-8')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.get_unique_handle()

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_unique_handle()

	def get_unique_handle(self):
		self.view.window().show_input_panel("Title:", "", self.set_unique_handle, None, None)

	def set_unique_handle(self, value):
		self.unique_handle = value
		self.get_default_group()

	def get_default_group(self):
		groups = []
		groups = requests.get('https://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
		for group in groups: # Is there a better way` to do this than iterating over the array?
			if group['name'] == 'Sublime':
				# print group['name']
				self.group_id = group['_id']
				# break
		# print "Selection:"
		# print self.view.sel() 
		self.create_new_snippet()

	def create_new_snippet(self): # Server not resolving all args passed for this route
		# print self.token
		# print self.new_snippet
		# print self.unique_handle
		new_snippet = {"user": self.token, "content": self.new_snippet, "unique_handle": self.unique_handle, "group": self.group_id}
		response = requests.post('https://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group_id), data=new_snippet ) # Change this route 
		if response.status_code == 200: 
			sublime.message_dialog("{0} successfully saved to CmdV Ninja!".format(self.unique_handle))
		else:
			sublime.error_message("Snippet failed to save. Please check internet connection or try a different title.")

##################################################################################################

class SearchgroupsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.accounts = self.settings.get("accounts")
		self.cmdv_ninja = self.accounts.get("cmdv_ninja")
		self.token = self.cmdv_ninja.get("token")
		self.groups = []
		self.snippet_collection = []
		self.edit = edit
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.get_collections()

	def set_token(self, value):
		self.token = value
		self.settings.set("accounts", { "cmdv_ninja": { "token": value } })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_collections()

	def get_collections(self):
		group_titles = []
		self.groups = requests.get('https://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
		for group in self.groups:
			group_titles.append(group['name'])
		self.view.window().show_quick_panel(group_titles, self.select_group)

	def select_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.get_search()

	def get_search(self):
		self.view.window().show_input_panel("Search", "", self.show_menu, self.fuzzy_search, None)

	def fuzzy_search(self, value): # Fix the get route to search a specific group
		self.snippet_titles = []
		self.snippet_collection = requests.get('https://cmdvninja.herokuapp.com/api/search?type=subl&limit=100&query={0}'.format(urllib.quote(value))).json()
		for snippet in self.snippet_collection:
			self.snippet_titles.append(snippet['unique_handle'])
		self.view.window().show_input_panel("Search", value, self.fuzzy_search, None, None)
		self.view.window().show_quick_panel(self.snippet_titles, self.copy_to_clipboard)

	def show_menu(self, value):
		self.view.window().show_quick_panel(self.snippet_titles, self.copy_to_clipboard)

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################

class LogoutCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("accounts").get("cmdv_ninja").get("token")
		if self.token != "":
			self.answer = sublime.ok_cancel_dialog('Are you sure you want to log out?')
			self.unauth()
		else:
			sublime.error_message("You are not currently logged in")

	def unauth(self):
		if self.answer == True:
			self.settings.set("accounts", { "cmdv_ninja": { "token": "" } })
			sublime.save_settings('cmdvninja.sublime-settings')
			sublime.status_message("Successfully logged out of CmdV Ninja")

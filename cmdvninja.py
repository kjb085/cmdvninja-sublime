import sublime, sublime_plugin
import requests
import urllib
import json
import webbrowser

# Add a way to clear default folder
# Add global search command
# Fix group based searching once there is a route to search individual groups (as of now this does the above no matter what group is selected)
# Clean up code by learning how to syncronously nest commands

# class AuthCommand(sublime_plugin.TextCommand):
# 	def run(self, edit):
# 		self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None)

# 	def set_token(self, value):
# 		self.token = value
# 		self.settings.set("cmdv_ninja", { "token": value })
# 		sublime.save_settings('cmdvninja.sublime-settings')
# 		return self.token

##################################################################################################################################

class OpenappCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		webbrowser.open_new_tab('http://cmdvninja.herokuapp.com/')

##################################################################################################################################

# Returns a menu of all a users snippets for the selected group
class MygroupsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.snippet_collection = []
		if self.token == "":
			# Really want to get this working
			# self.token = sublime.run_command('auth') 
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.get_collections()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_collections()

	def get_collections(self):
		group_titles = []
		self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
		for group in self.groups:
			group_titles.append(group['name'])
		self.view.window().show_quick_panel(group_titles, self.select_group)

	def select_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['_id'])).json()
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

##################################################################################################################################

# Creates a new snippet on the database from the clipboard
class CreatesnipCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.new_snippet = sublime.get_clipboard().encode('utf-8')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.get_unique_handle()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value )
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_unique_handle()

	def get_unique_handle(self):
		self.view.window().show_input_panel("Title:", "", self.set_unique_handle, None, None)

	def set_unique_handle(self, value):
		self.unique_handle = value
		self.get_default_group()

	def get_default_group(self):
		groups = []
		groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
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
		response = requests.post('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group_id), data=new_snippet ) # Change this route 
		if response.status_code == 200: 
			sublime.message_dialog("{0} successfully saved to CmdV Ninja!".format(self.unique_handle))
		else:
			sublime.error_message("Snippet failed to save. Please check internet connection or try a different title.")

##################################################################################################################################

class SearchgroupsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.snippet_collection = []
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.get_collections()

	def set_token(self, value):
		self.token = value
		self.settings.set("cmdv_ninja", { "token": value })
		sublime.save_settings('cmdvninja.sublime-settings')
		self.get_collections()

	def get_collections(self):
		group_titles = []
		self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
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
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/search?type=subl&limit=100&query={0}'.format(urllib.quote(value))).json()
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

##################################################################################################################################

class LogoutCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		if self.token != "":
			self.answer = sublime.ok_cancel_dialog('Are you sure you want to log out?')
			self.unauth()
		else:
			sublime.error_message("You are not currently logged in")

	def unauth(self):
		if self.answer == True:
			self.settings.set("token", "")
			sublime.save_settings('cmdvninja.sublime-settings')
			sublime.status_message("Successfully logged out of CmdV Ninja")

##################################################################################################################################
# Every command from here and below is mapped to cmd + shift + a number between digit between 1 - 0 on the keyboard and the user can set the folder of their that each is mapped to the first time that they use the hotkey.
class FolderoneCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_1')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_1" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FoldertwoCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_2')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_2" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FolderthreeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_3')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else:
			self.select_group()

	def set_token(self, value):
		self.token = value1
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_3" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FolderfourCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_4')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_4" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FolderfiveCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_5')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_5" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FoldersixCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_6')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_6" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FoldersevenCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_7')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_7" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FoldereightCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_8')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_8" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FoldernineCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_9')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_9" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))

##################################################################################################################################

class FolderzeroCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.settings = sublime.load_settings('cmdvninja.sublime-settings')
		self.token = self.settings.get("token")
		self.groups = []
		self.group = self.settings.get('folder_0')
		if self.token == "":
			self.view.window().show_input_panel("Authentication Token:", "", self.set_token, None, None) 
		else: 
			self.select_group()

	def set_token(self, value):
		self.token = value
		self.settings.set("token", value)
		sublime.save_settings('cmdvninja.sublime-settings')
		self.select_group()

	def select_group(self):
		if self.group["id"] == "":
			sublime.message_dialog("No group mapped to this hot key. Please select a group.")
			group_titles = []
			self.groups = requests.get('http://cmdvninja.herokuapp.com/api/users/{0}/groups'.format(self.token)).json()
			for group in self.groups: 
				group_titles.append(group['name'])
			self.view.window().show_quick_panel(group_titles, self.set_group)
		else:
			self.show_group_snippets()

	def set_group(self, value):
		if value > -1:
			self.group = self.groups[value]
			self.group['id'] = self.group["_id"] # This is so hacky
			self.settings.set("folder_0" , {"name": self.group["name"], "id": self.group["id"] })
			sublime.save_settings('cmdvninja.sublime-settings')
			self.show_group_snippets()

	def show_group_snippets(self):
		snippet_titles = []
		self.snippet_collection = requests.get('http://cmdvninja.herokuapp.com/api/groups/{0}/snippets'.format(self.group['id'])).json()
		if len(self.snippet_collection) > 0:
			for snippet in self.snippet_collection:
				snippet_titles.append(snippet['unique_handle'])
			self.view.window().show_quick_panel(snippet_titles, self.copy_to_clipboard)
			sublime.status_message("Currently showing snippets from {0}".format(self.group['name']))
		else:
			sublime.error_message('Currently no code snippets in this group')

	def copy_to_clipboard(self, value):
		if value > -1:
			self.snippet = self.snippet_collection[value]
			sublime.set_clipboard(self.snippet['content'])
			sublime.status_message("{0} successfully copied to the clipboard!".format(self.snippet['unique_handle']))


import json
import os
import pickle
import random
import time
import urllib.request
import uuid
from collections import defaultdict
from functools import partial, wraps

import mongoengine as mdb
import telebot
import telegram as tg

from config import *
from data_storage import BotUser, MusicTrack
import music_operations as music;
import profile_operations as profile;
import service_operations as service;

GREETING_KEYWORDS = ["hello", "hi", "greetings", "sup", "whats up", "hey"]
GREETING_RESPONSES = ["Hi there", "Greetings", "Salute", "Hello" "Loading...Here I am!"]


class Responder:
	action_dictionary = service.tree();

	# Connect service common methods
	insert_callback = service.insert_callback;
	edit_callback = service.edit_callback;
	edit_action = service.edit_action
	cancel = service.cancel;
	get_genres_menu = service.get_genres_menu;
	add_genres_actions = service.add_genres_actions;
	set_genres_markup = service.set_genres_markup;
	add_genre = service.add_genre;
	clear_genres = service.clear_genres;
	# Connect on music operation methods
	add_crud_actions = music.add_crud_actions;
	get_main_menu = music.get_main_menu;
	view_music_collection = music.view_music_collection;
	delete_action = music.delete_action;
	delete_yes = music.delete_yes;
	publish = music.publish;
	request_music = music.request_music;
	# Connect on user profile operation methods;
	add_profile_actions = profile.add_profile_actions;
	get_user = profile.get_user;
	registration = profile.registration;
	save_profile = profile.save_profile;
	save_yes = profile.save_yes;

	def __init__(self, bot):
		self.bot = bot

	@service.send_typing_action
	def respond(self, message):
		queried_users = BotUser.objects(chat_id=message.chat.id);
		if not queried_users:
			self.registration(message);
		if any(word in message.text.lower() for word in ["init", "ready"]):
			self.bot.send_message(message.chat.id, "Greetings Master. I am ready to serve you!", reply_markup=self.get_main_menu(queried_users.get()));
		if message.text == music.INSERT_REPLY:
			self.bot.send_message(message.chat.id, "Send me a link to the track, if you please");
			self.bot.register_next_step_handler(message, self.insert_callback);
		elif message.text == music.VIEW_REPLY:
			self.view_music_collection(message);
		elif message.text == music.REQUEST_REPLY:
			self.request_music(message);

	def subscribe_actions(self, call):
		action_nodes = call.data.split("/");
		if MusicTrack.objects(pk=action_nodes[-1]):
			document = MusicTrack.objects(pk=action_nodes[-1]).get();
		elif BotUser.objects(pk=action_nodes[-1]):
			document = BotUser.objects(pk=action_nodes[-1]).get();
		self.get_action(action_nodes[:-1])(call, document);

	def command_handler(self, command, message):
		if command == "start":
			self.bot.send_message(message.chat.id, "Greetings my friend! I'm here to help you share music with your friends. Let's begin then, shall we?");

	def get_action(self, nodes):
		action_node = self.action_dictionary;
		for node in nodes:
			action_node = action_node[node];
		return action_node;

	def init_action_dictionary(self):
		self.add_profile_actions();
		self.add_crud_actions();
		self.add_genres_actions();
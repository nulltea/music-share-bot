import json;
import random;
import os;
import urllib.request;
import time;
import uuid;
import pickle;
from functools import partial, wraps;
from collections import defaultdict;

import mongoengine as mdb
import telebot
import telegram as tg;

from config import *;
from data_storage import BotUser, MusicTrack

GREETING_KEYWORDS = ["hello", "hi", "greetings", "sup", "whats up", "hey"]
GREETING_RESPONSES = ["Hi there", "Greetings", "Salute", "Hello" "Loading...Here I am!"]


def send_typing_action(func):
	@wraps(func)
	def command_func(self, message, *args, **kwargs):
		self.bot.send_chat_action(chat_id=message.chat.id, action=tg.ChatAction.TYPING)
		return func(self, message, *args, **kwargs)
	return command_func


def tree():
	return defaultdict(tree)


class Responder:
	action_dictionary = tree();
	insert_reply = "Add music track";
	view_reply = "View music collection";

	def __init__(self, bot):
		self.bot = bot

	@send_typing_action
	def respond(self, message):
		if not BotUser.objects(username=message.from_user.username):
			self.registration(message);
		if any(word in message.text.lower() for word in ["init", "ready"]):
			self.bot.send_message(message.chat.id, "Greetings Master. I am ready to serve you!", reply_markup=self.get_creator_menu());
		if message.text == self.insert_reply:
			self.bot.send_message(message.chat.id, "Send me a link to the track, if you please");
			self.bot.register_next_step_handler(message, self.insert_callback);
		elif message.text == self.view_reply:
			self.view_music_collection(message);

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

	def registration(self, message):
		self.bot.send_message(message.chat.id, "Perfect. First, can you check this information about yourself that I've gathered from your profile?");
		new_user = BotUser(
			chat_id=message.chat.id,
			username=message.from_user.username,
			first_name=message.from_user.first_name,
			last_name=message.from_user.last_name
		);
		new_user.set_profile_info(message);
		new_user.save();
		self.bot.send_photo(message.chat.id, new_user.profile_picture, new_user.generate_message(),
			reply_markup=new_user.get_edit_menu(), parse_mode='Markdown');

	def get_action(self, nodes):
		action_node = self.action_dictionary;
		for node in nodes:
			action_node = action_node[node];
		return action_node;

	def view_music_collection(self, message):
		for music_track in MusicTrack.objects(is_used=False):
			self.bot.send_photo(message.chat.id, music_track.cover_image, music_track.generate_message(), reply_markup=music_track.get_edit_menu(), parse_mode='Markdown');

	@send_typing_action
	def insert_callback(self, message):
		user = BotUser.objects(chat_id=message.chat.id).get();
		music_track = MusicTrack(publisher=user);
		music_track.add_link(message.text);
		try:
			music_track.save();
		except mdb.errors.NotUniqueError as e:
			music_track = MusicTrack.objects(track_id=music_track.track_id).get();
			self.bot.send_message(message.chat.id, "Track was already added. Here it is:");
		self.bot.send_photo(message.chat.id, music_track.cover_image, music_track.generate_message(), reply_markup=music_track.get_edit_menu(), parse_mode='Markdown');

	@send_typing_action
	def edit_callback(self, message, property, document, call):
		attr = getattr(document, property)
		if callable(attr):
			attr(message.text)
		elif isinstance(attr, list):
			attr.extend(message.text.split(","));
		else:
			setattr(document, property, message.text);
		document.save();
		menu = self.get_genres_menu(document) if property == "genres" else document.get_edit_menu();
		self.bot.edit_message_caption(document.generate_message(), call.message.chat.id, call.message.message_id, reply_markup=menu, parse_mode='Markdown');

	def get_creator_menu(self):
		menu = telebot.types.ReplyKeyboardMarkup();
		menu.row(self.insert_reply);
		menu.row(self.view_reply);
		return menu;

	def edit_action(self, call, document, hint, property):
		self.bot.send_message(call.message.chat.id, hint, reply_markup=telebot.types.ForceReply());
		self.bot.register_next_step_handler(call.message, self.edit_callback, property, document, call);

	def delete_action(self, call, track):
		menu = telebot.types.InlineKeyboardMarkup();
		menu.row(telebot.types.InlineKeyboardButton(text="Yes", callback_data=f"crud/delete/yes/{track.pk}"),
			telebot.types.InlineKeyboardButton(text="No", callback_data=f"crud/delete/no/{track.pk}"));
		self.bot.edit_message_caption("Are you sure about that?", call.message.chat.id, call.message.message_id, reply_markup=menu);

	def delete_yes(self, call, track):
		track.delete();
		self.bot.delete_message(call.message.chat.id, call.message.message_id);

	def cancel(self, call, track):
		self.bot.edit_message_caption(track.generate_message(), call.message.chat.id, call.message.message_id,
			reply_markup=track.get_edit_menu(),
			parse_mode='Markdown');

	def save_profile(self, call, profile):
		menu = telebot.types.InlineKeyboardMarkup();
		menu.row(telebot.types.InlineKeyboardButton(text="Yes", callback_data=f"profile/save/yes/{profile.pk}"),
			telebot.types.InlineKeyboardButton(text="No", callback_data=f"profile/save/no/{profile.pk}"));
		self.bot.edit_message_caption("Are you sure about that?", call.message.chat.id, call.message.message_id, reply_markup=menu);

	def save_yes(self, call, profile):
		self.bot.edit_message_caption("Great we are done!", call.message.chat.id, call.message.message_id);

	def get_genres_menu(self, document):
		menu = telebot.types.InlineKeyboardMarkup();
		for i in range(4):
			row = [];
			for j in range(1, 4):
				genre = MUSIC_GENRES[j + i * 3 - 1];
				if genre in document.genres:
					continue;
				row.append(telebot.types.InlineKeyboardButton(text=genre, callback_data=f"profile/genres/{genre}/{document.pk}"));
			menu.row(*row);
		menu.row(telebot.types.InlineKeyboardButton(text="Add other", callback_data=f"profile/genres/other/{document.pk}"),
			telebot.types.InlineKeyboardButton(text="Clear", callback_data=f"profile/genres/clear/{document.pk}"));
		menu.row(telebot.types.InlineKeyboardButton(text="Done", callback_data=f"profile/genres/done/{document.pk}"));
		return menu;

	def set_genres_markup(self, call, document):
		selected_genres = "-" if document.genres is None or not any(document.genres) else ", ".join(document.genres);
		try:
			self.bot.edit_message_caption(f"Selected geners: *{selected_genres}*\nChoose music genres or add other ones", call.message.chat.id,
				call.message.message_id, reply_markup=self.get_genres_menu(document), parse_mode='Markdown');
		except:
			pass;

	def add_genre(self, call, document, genre):
		document.genres.append(genre);
		document.save();
		self.set_genres_markup(call, document);

	def clear_genres(self, call, document):
		document.genres = [];
		document.save();
		self.set_genres_markup(call, document);

	def init_action_dictionary(self):
		self.add_profile_actions();
		self.add_crud_actions();
		self.add_genres_actions();

	def add_genres_actions(self):
		for document in ["profile", "crud"]:
			for genre in MUSIC_GENRES:
				self.action_dictionary[document]["genres"][genre] = partial(self.add_genre, genre=genre);
			self.action_dictionary[document]["genres"]["other"] = partial(self.edit_action,
			hint="Wow! You know more than that, what is it?", property="genres");
			self.action_dictionary[document]["genres"]["clear"] = partial(self.clear_genres);
			self.action_dictionary[document]["genres"]["done"] = partial(self.cancel);

	def add_profile_actions(self):
		self.action_dictionary["profile"]["firstname"] = partial(self.edit_action,
			hint="Sorry, what should I call you then?", property="first_name");
		self.action_dictionary["profile"]["lastname"] = partial(self.edit_action,
			hint="Sorry, what should I call you then?", property="last_name");
		self.action_dictionary["profile"]["bio"] = partial(self.edit_action,
			hint="Great can't wait to read more about you, so?", property="bio");
		self.action_dictionary["profile"]["genres"]["choose"] = partial(self.set_genres_markup);
		self.action_dictionary["profile"]["save"]["ask"] = partial(self.save_profile);
		self.action_dictionary["profile"]["save"]["yes"] = partial(self.save_yes);
		self.action_dictionary["profile"]["save"]["no"] = partial(self.cancel);

	def add_crud_actions(self):
		self.action_dictionary["crud"]["artist"] = partial(self.edit_action,
			hint="Ok, now send me them (by comma)", property="artists");
		self.action_dictionary["crud"]["album"] = partial(self.edit_action,
			hint="Sure, what`s the album name?", property="album");
		self.action_dictionary["crud"]["genres"]["choose"] = partial(self.set_genres_markup);
		self.action_dictionary["crud"]["description"] = partial(self.edit_action,
			hint="Sure, now you can enter the description", property="description");
		self.action_dictionary["crud"]["link"] = partial(self.edit_action,
			hint="Not a problem, please send me one", property="add_link");
		self.action_dictionary["crud"]["delete"]["ask"] = partial(self.delete_action);
		self.action_dictionary["crud"]["delete"]["yes"] = partial(self.delete_yes);
		self.action_dictionary["crud"]["delete"]["no"] = partial(self.cancel);

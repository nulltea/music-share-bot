import json;
import random;
import os;
import urllib.request;
import time;
import uuid;
import pickle;
from functools import partial, wraps;
from collections import defaultdict;

import mongoengine as mdb;
import telebot;
import telegram as tg;

from config import *;
from data_storage import BotUser, MusicTrack;


def tree():
	return defaultdict(tree)


def send_typing_action(func):
	@wraps(func)
	def command_func(self, message, *args, **kwargs):
		#self.bot.send_chat_action(chat_id=message.chat.id, action=tg.ChatAction.TYPING)
		return func(self, message, *args, **kwargs)
	return command_func


@send_typing_action
def insert_callback(self, message):
	user = self.get_user(message);
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
	try:
		self.bot.edit_message_caption(document.generate_message(), call.message.chat.id, call.message.message_id, reply_markup=menu, parse_mode='Markdown');
	except:
		pass;


def edit_action(self, call, document, hint, property):
	self.bot.send_message(call.message.chat.id, hint, reply_markup=telebot.types.ForceReply());
	self.bot.register_next_step_handler(call.message, self.edit_callback, property, document, call);


def cancel(self, call, track):
	self.bot.edit_message_caption(track.generate_message(), call.message.chat.id, call.message.message_id,
		reply_markup=track.get_edit_menu(),
		parse_mode='Markdown');


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
	document.genres.append(genre.lower());
	document.save();
	self.set_genres_markup(call, document);


def clear_genres(self, call, document):
	document.genres = [];
	document.save();
	self.set_genres_markup(call, document);


def add_genres_actions(self):
	for document in ["profile", "crud"]:
		for genre in MUSIC_GENRES:
			self.action_dictionary[document]["genres"][genre] = partial(self.add_genre, genre=genre);
		self.action_dictionary[document]["genres"]["other"] = partial(self.edit_action,
		hint="Wow! You know more than that, what is it?", property="genres");
		self.action_dictionary[document]["genres"]["clear"] = self.clear_genres;
		self.action_dictionary[document]["genres"]["done"] = self.cancel;

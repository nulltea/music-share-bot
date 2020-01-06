import json;
import os;
import pickle;
import random;
import time;
import urllib.request;
import uuid;
from collections import defaultdict;
from functools import partial, wraps;

import mongoengine as mdb
import telebot;
import telegram as tg;

from config import *
from data_storage import BotUser, MusicTrack

INSERT_REPLY = "Add music track";
VIEW_REPLY = "View music collection";
REQUEST_REPLY = "Request music";


def get_main_menu(self, user=None):
	menu = telebot.types.ReplyKeyboardMarkup();
	menu.row(INSERT_REPLY, VIEW_REPLY);
	if user and MusicTrack.objects(publisher=user).count() >= 1:
		menu.row(REQUEST_REPLY);
	return menu;


def add_crud_actions(self):
	self.action_dictionary["crud"]["artist"] = partial(self.edit_action,
		hint="Ok, now send me them (by comma)", property="artists");
	self.action_dictionary["crud"]["album"] = partial(self.edit_action,
		hint="Sure, what`s the album name?", property="album");
	self.action_dictionary["crud"]["genres"]["choose"] = partial(self.set_genres_markup);
	self.action_dictionary["crud"]["description"] = partial(self.edit_action,
		hint="Sure, now you can enter the description", property="description");
	self.action_dictionary["crud"]["link"]["menu"] = self.set_link_markup;
	self.action_dictionary["crud"]["link"]["add"] = partial(self.edit_action,
		hint="Not a problem, please send me one", property="add_link");
	self.action_dictionary["crud"]["link"]["done"] = self.cancel;
	self.action_dictionary["crud"]["delete"]["ask"] = self.delete_action;
	self.action_dictionary["crud"]["delete"]["yes"] = self.delete_yes;
	self.action_dictionary["crud"]["delete"]["no"] = self.cancel;
	self.action_dictionary["crud"]["publish"] = self.publish;


def get_link_menu(track):
	menu = telebot.types.InlineKeyboardMarkup();
	button_row = [];
	for service in track.track_urls:
		button_row.append(telebot.types.InlineKeyboardButton(text=service, url=track.track_urls[service]));
	menu.row(*button_row)
	menu.add(telebot.types.InlineKeyboardButton(text="Add link", callback_data=f"crud/link/add/{track.pk}"));
	menu.add(telebot.types.InlineKeyboardButton(text="Done", callback_data=f"crud/link/done/{track.pk}"));
	return menu;


def view_music_collection(self, message):
	for music_track in MusicTrack.objects(__raw__={"$expr": {"$lte": [{"$size": "$seen_by"}, 0]}}):
		self.bot.send_photo(message.chat.id, music_track.cover_image, music_track.generate_message(), reply_markup=music_track.get_edit_menu(), parse_mode='Markdown');


def delete_action(self, call, track):
	menu = telebot.types.InlineKeyboardMarkup();
	menu.row(telebot.types.InlineKeyboardButton(text="Yes", callback_data=f"crud/delete/yes/{track.pk}"),
		telebot.types.InlineKeyboardButton(text="No", callback_data=f"crud/delete/no/{track.pk}"));
	self.bot.edit_message_caption("Are you sure about that?", call.message.chat.id, call.message.message_id, reply_markup=menu);


def delete_yes(self, call, track):
	track.delete();
	self.bot.delete_message(call.message.chat.id, call.message.message_id);


def set_link_markup(self, call, track):
	added_services = "-" if track.track_urls is None or not any(track.track_urls) else ", ".join(track.track_urls);
	self.bot.edit_message_caption(f"Added services: *{added_services}*", call.message.chat.id,
			call.message.message_id, reply_markup=get_link_menu(track), parse_mode='Markdown');


def publish(self, call, track):
	if track.available:
		return;
	user = self.get_user(call.message);
	track.available = True;
	track.save();
	try:
		self.bot.edit_message_caption(document.generate_message(), call.message.chat.id, call.message.message_id, reply_markup=menu, parse_mode='Markdown');
	except:
		pass;
	if MusicTrack.objects(publisher=user).count() == 1:
		self.bot.send_message(call.message.chat.id, f"Nicely done {user.first_name}. As you published your first music track - you now can request ones!",
		reply_markup=self.get_main_menu(user));

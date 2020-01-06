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


def add_feed_actions(self):
	self.action_dictionary["feed"]["comment"]["add"] = self.comment_action;
	self.action_dictionary["feed"]["like"] = self.delete_yes;
	self.action_dictionary["feed"]["dislike"] = self.delete_yes;


def get_post_menu(track):
	menu = telebot.types.InlineKeyboardMarkup();
	button_row = [];
	for service in track.track_urls:
		button_row.append(telebot.types.InlineKeyboardButton(text=service, url=track.track_urls[service]));
	menu.row(*button_row)
	menu.add(telebot.types.InlineKeyboardButton(text="Comment", callback_data=f"feed/comment/add/{track.pk}"));
	return menu;


def request_music(self, message):
	user = self.get_user(message);
	queried_tracks = MusicTrack.objects(available=True, seen_by__nin=[user])		# publisher__ne=user;
	if queried_tracks.count() == 0:
		self.bot.send_message(message.chat.id, "Sorry. Not any");
	else:
		music_track = queried_tracks.first();
		self.bot.send_photo(message.chat.id, music_track.cover_image, music_track.generate_message(), reply_markup=get_post_menu(music_track), parse_mode='Markdown');


def comment_action(self, call, track):
	self.bot.send_message(call.message.chat.id, "Hope you like it, what do you think?", reply_markup=telebot.types.ForceReply());
	self.bot.register_next_step_handler(call.message, self.comment_callback, track);


def comment_callback(self, message, track):
	user = self.get_user(message);
	track.comments[user.username] = message.text;
	self.notify_publisher(track, message, from_user=user);


def notify_publisher(self, track, message, from_user):
	self.bot.send_message(track.publisher.chat_id, f"*{from_user.first_name} {from_user.last_name}* just commented track (*{track.track_id}*) you added:", parse_mode='Markdown');
	self.bot.forward_message(track.publisher.chat_id, message.chat.id, message.message_id);


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
from data_storage import BotUser


def get_user(self, message):
		return BotUser.objects(chat_id=message.chat.id).get();


def add_profile_actions(self):
	self.action_dictionary["profile"]["firstname"] = partial(self.edit_action,
		hint="Sorry, what should I call you then?", property="first_name");
	self.action_dictionary["profile"]["lastname"] = partial(self.edit_action,
		hint="Sorry, what should I call you then?", property="last_name");
	self.action_dictionary["profile"]["bio"] = partial(self.edit_action,
		hint="Great can't wait to read more about you, so?", property="bio");
	self.action_dictionary["profile"]["genres"]["choose"] = self.set_genres_markup;
	self.action_dictionary["profile"]["save"]["ask"] = self.save_profile;
	self.action_dictionary["profile"]["save"]["yes"] = self.save_yes;
	self.action_dictionary["profile"]["save"]["no"] = self.cancel;


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


def save_profile(self, call, profile):
	menu = telebot.types.InlineKeyboardMarkup();
	menu.row(telebot.types.InlineKeyboardButton(text="Yes", callback_data=f"profile/save/yes/{profile.pk}"),
		telebot.types.InlineKeyboardButton(text="No", callback_data=f"profile/save/no/{profile.pk}"));
	self.bot.edit_message_caption("Are you sure about that?", call.message.chat.id, call.message.message_id, reply_markup=menu);


def save_yes(self, call, profile):
	user = get_user(message);
	self.bot.edit_message_caption(f"Awesome. So nice to meet you {user.first_name}", call.message.chat.id, call.message.message_id);
	self.bot.edit_message_caption("Now you can add your music tracks to shared collection!", call.message.chat.id, call.message.message_id, reply_markup=self.get_main_menu());

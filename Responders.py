import json;
import random;
import time;
import uuid;
from functools import *;
from collections import Iterable as iter;

import mongoengine as mdb
import telebot

from data_storage import ChatsInfo, MusicTrack

GREETING_KEYWORDS = ["hello", "hi", "greetings", "sup", "whats up", "hey"]
GREETING_RESPONSES = ["Hi there", "Greetings", "Salute", "Hello" "Loading...Here I am!"]


class Responder:
	action_dictionary = {};
	insert_reply = "Add music track";
	view_reply = "View music collection";

	def __init__(self, bot):
		self.bot = bot

	def respond(self, message):
		if any(word in message.text.lower() for word in ["init", "ready"]):
			self.bot.send_message(message.chat.id, "Greetings Master. I am ready to serve you!", reply_markup=self.get_creator_menu());
		if message.text == self.insert_reply:
			self.bot.send_message(message.chat.id, "Send me a link to the track, if you please");
			self.bot.register_next_step_handler(message, self.insert_callback);
		elif message.text == self.view_reply:
			self.view_music_collection(message);

	def subscribe_actions(self, call):
		self.action_dictionary[call.data](call=call);

	def command_handler(self, command, message):
		if command == "start":
			self.bot.send_message(message.chat.id, "Greetings my friend! I'm here to help you share music with your friends. Let's begin then, shall we?");

	def view_music_collection(self, message):
		for music_track in MusicTrack.objects(is_used=False):
			self.bot.send_photo(message.chat.id, music_track.cover_image, music_track.generate_message(), reply_markup=self.get_track_menu(music_track), parse_mode='Markdown');

	def insert_callback(self, message):
		music_track = MusicTrack();
		music_track.add_link(message.text);
		try:
			music_track.save();
		except mdb.errors.NotUniqueError as e:
			music_track = MusicTrack.objects(track_id=music_track.track_id).get();
			self.bot.send_message(message.chat.id, "Track was already added. Here it is:");
		self.bot.send_photo(message.chat.id, music_track.cover_image, music_track.generate_message(), reply_markup=self.get_track_menu(music_track), parse_mode='Markdown');

	def edit_callback(self, message, track_property, track):
		attr = getattr(track, track_property)
		if callable(attr):
			attr(message.text)
		elif isinstance(attr, iter):
			attr.append(message.text);
		else:
			setattr(track, track_property, message.text);
		track.save();
		self.bot.send_message(message.chat.id, random.choice(["Saved", "Done", "Yep", "Nice", "Greate"]));

	def get_creator_menu(self):
		menu = telebot.types.ReplyKeyboardMarkup();
		menu.row(self.insert_reply);
		menu.row(self.view_reply);
		return menu;

	def edit_action(self, call, hint, property, track):
		self.bot.send_message(call.message.chat.id, hint);
		self.bot.register_next_step_handler(call.message, self.edit_callback, property, track);

	def del_action(self, call, track, parent_menu):
		def func(call, track):
			track.delete();
			self.bot.delete_message(call.message.chat.id, call.message.message_id);
		menu = telebot.types.InlineKeyboardMarkup();

		act_uuid = uuid.uuid4().hex;
		menu.add(telebot.types.InlineKeyboardButton(text="Yes, do it!", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid: partial(func, track=track)});

		act_uuid = uuid.uuid4().hex;
		menu.add(telebot.types.InlineKeyboardButton(text="No, never mind", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid: lambda call: self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=parent_menu)});

		self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=menu);

	def get_track_menu(self, track):
		menu = telebot.types.InlineKeyboardMarkup();

		act_uuid = uuid.uuid4().hex;
		prefix = "Add" if any(track.artists) else "Set";
		menu.add(telebot.types.InlineKeyboardButton(text=f"{prefix} artists", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid:
			partial(self.edit_action, hint="Ok, now send me them (by comma)", property="artists", track=track)});

		act_uuid = uuid.uuid4().hex;
		prefix = "Set" if track.album is None or track.album == "" else "Edit";
		menu.add(telebot.types.InlineKeyboardButton(text=f"{prefix} album", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid:
			partial(self.edit_action, hint="Sure, what`s the album name?", property="album", track=track)});

		act_uuid = uuid.uuid4().hex;
		prefix = "Add" if any(track.genres) else "Set";
		menu.add(telebot.types.InlineKeyboardButton(text=f"{prefix} genres", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid:
			partial(self.edit_action, hint="Fine, then write them up (by comma)", property="genres", track=track)});

		act_uuid = uuid.uuid4().hex;
		prefix = "Set" if track.description is None or track.description == "" else "Edit";
		menu.add(telebot.types.InlineKeyboardButton(text=f"{prefix} description", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid:
			partial(self.edit_action, hint="Sure, now you can enter the description", property="genres", track=track)});

		act_uuid = uuid.uuid4().hex;
		menu.add(telebot.types.InlineKeyboardButton(text="Add link", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid:
			partial(self.edit_action, hint="Not a problem, please send me one", property="genres", track=track)});

		act_uuid = uuid.uuid4().hex;
		menu.add(telebot.types.InlineKeyboardButton(text="Remove from collection", callback_data=act_uuid));
		self.action_dictionary.update({act_uuid:
			partial(self.del_action, track=track, parent_menu=menu)});
		return menu;


class AdminResponder(Responder):
	def __init__(self, bot):
		self.bot = bot
		super().__init__()

	def respond(self, message):
		success, respond = Responder.check_for_greeting(message.text)
		if success:
			self.bot.send_message(message.chat.id, respond);

	def subscribe_actions(self, call):
		pass;

	@staticmethod
	def check_for_greeting(sentence):
		for word in sentence.split(' '):
			if word.lower() in GREETING_KEYWORDS:
				return True, random.choice(GREETING_RESPONSES)
		return False, '';


class UserResponder(Responder):
	NEW_TRACK_STARTERS = ["Let me think about it ... 🤔", "Hmm, what do I have here...", "I bring to your attention", "I really like this🤩", "Let's start with this one", "Uff, get ready!", "Your friend has a great taste 👝 "," For such a nothing nothing is sorry! 💖 "];
	NEW_TRACK_IMPRESSIONS = ["How do you like one?", "Tell me your impressions", "I will wait for your impressions", "What do you think?", "Do not forget to comment", "I see that you liked it!"];

	music_library = MusicTrack();
	chats_info = ChatsInfo();

	def __init__(self, bot):
		self.bot = bot
		super().__init__(bot)

	def respond(self, message):
		sentence = message.text;
		# success, respond = self.check_for_greeting(sentence);
		if any(word in message.text.lower() for word in ["music", "track", "techno", "new one", "listen", "🎶", "🎵"]):
			track = self.music_library.get_new_track();
			self.send_music_track(message, track);
		elif any(word in message.text.lower() for word in ["thx", "thanks"]):
			self.bot.send_message(message.chat.id, "You're welcome");

	def subscribe_actions(self, call):
		params = call.data.split('_');
		if params[0] == "imp":
			self.bot.send_message(call.message.chat.id, random.choice(["Recording🎙", "I’m listening to you🎧", "Go for it", "Listening you carefully🎧"]));
			self.bot.register_next_step_handler(call.message, self.impression_input, params[1]);
		elif params[0] == "artist":
			self.bot.send_message(call.message.chat.id, random.choice(["Нга, поищем..", "Дай ка подумать", "Милиѝекундочку"]));
			track = self.music_library.get_by_artist(params[1]);
			if track is None:
				self.bot.send_message(call.message.chat.id, "Увы, больше трѝков от {0} нет...Но ѝ передам Тимофею и когда он добавит ты об ѝтом неприменно узнаешь😉".format(params[1]));
				self.bot.send_message(call.message.chat.id, "Н пока могу предложить тебе что-то другое");
				self.send_music_track(call.message, self.music_library.get_new_track());
				self.bot.send_message(self.chats_info.get_chat_id("timothy_y"), "Alert🚨🚨🚨\nДорогаѝ Наѝтѝ хочет еще музыки от {0}. Тебе ѝтоит занѝтьѝѝ ѝтим!".format(params[1]));
			self.send_music_track(call.message, track);

	def send_music_track(self, message, track):
		if track is None:
			self.bot.send_message(message.chat.id, "😢😢😢");
			self.bot.send_message(message.chat.id, "Извини {0}, но новый музыки пока нет. Я передам Тимофею и когда он добавт ты об ѝтом неприменно узнаешь😉".format(random.choice(self.NICKNAMES)));
			self.bot.send_message(self.chats_info.get_chat_id("timothy_y"), "Alert🚨🚨🚨\nЗакончилаѝь музыка длѝ любимой Наѝти. Тебе ѝтоит занѝтьѝѝ ѝтим!");
		else:
			self.chats_info.set_last_track(LOVER_USER_ID, track["track_id"]);
			self.bot.send_message(message.chat.id, random.choice(self.NEW_TRACK_STARTERS));
			track_menu = telebot.types.InlineKeyboardMarkup();
			track_menu.add(telebot.types.InlineKeyboardButton(text="Apple Music🎵", url=track["track_url"]));
			self.bot.send_message(message.chat.id, "#MusicFromTimothy\n" + track["track_id"].replace("-", " ").title() + random.choice([" от ", " - ", " в иѝполнении "]) + "#" + track["artist"], reply_markup=track_menu);
			# self.bot.send_message(message.chat.id, "Сѝылка на проѝлушивание:\n{0}".format(track["track_url"]));
			if track["description"] != "-":
				self.bot.send_message(message.chat.id, track["description"]);
			impressions = telebot.types.InlineKeyboardMarkup();
			impressions.add(telebot.types.InlineKeyboardButton(text="Раѝѝказать впечетлениѝ", callback_data="imp_" + track["track_id"]));
			impressions.add(telebot.types.InlineKeyboardButton(text="Еще от {0}".format(track["artist"]), callback_data="artist_" + track["artist"]));
			self.bot.send_message(message.chat.id, random.choice(self.NEW_TRACK_IMPRESSIONS), reply_markup=impressions)

	def check_for_greeting(self, sentence):
		for word in sentence.words:
			if word.lower() in GREETING_KEYWORDS:
				return True, "Приветѝтвую тебѝ, Наѝтѝ. Да - ѝ знаю, кто ты. Создатель запрограмировал менѝ определѝть тебѝ из миллиардов людей."
		return False, '';

	def impression_input(self, message, track_id):
		self.music_library.rate_track(track_id, message.text);
		self.send_feedback(message.text, track_id)
		self.bot.send_message(message.chat.id, random.choice(["Спаѝибо😘", "Леѝтно", "Передам", "Краѝиво ѝказано!😝", "Рад, что тебе понравилоѝь😉"]));

	def send_feedback(self, comment, track_id):
		creator_chat_id = self.chats_info.get_chat_id("timothy_y");
		self.bot.send_message(creator_chat_id, "#NastiaImpressions\nНаша любимаѝ Наѝтѝ проѝлушала и оценила трѝк {0}".format(track_id.replace("-", " ").title()));
		self.bot.send_message(creator_chat_id, "Цитирую:\n{0}".format(comment));

	def get_lover_menu(self):
		menu = telebot.types.ReplyKeyboardMarkup();
		menu.row("Попроѝить музыку🎵");
		return menu;

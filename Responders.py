import random;
import json;
import telebot
import pymongo;
import time;
from DataStorage import MusicTrack;
from DataStorage import ChatsInfo;

CREATOR_USER_ID = "timothy_y";
LOVER_USER_ID = "il_nitski";
FRIEND_USER_ID = "liza"

GREETING_KEYWORDS = ["hello", "hi", "greetings", "sup", "whats up","hey"]
GREETING_RESPONSES = ["Hi there", "Greetings", "Salute", "Hello" "Loadig...Here I am!"]

class Responder:
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

class AdminResponder(Responder):
	insert_reply = "Add music track";
	remove_reply = "Remove music track";
	edit_reply = "Edit music track info";
	view_reply = "View music collection";

	music_library = MusicLibrary();

	def __init__(self, bot):
		self.bot = bot
		super().__init__(bot)

	def respond(self, message):
		super().respond(message);
		if any(word in message.text.lower() for word in ["init", "ready"]):
			self.bot.send_message(message.chat.id, "Greetings Master. I am ready to serve you!", reply_markup=self.get_creator_menu());
		if message.text == self.insert_reply:
			self.bot.send_message(message.chat.id, "Send me a link to the track, if you please");
			self.bot.register_next_step_handler(message, self.insert_callback);
		elif message.text == self.edit_reply:
			self.bot.send_message(message.chat.id, "Sure. Specify track id for me");
			self.bot.register_next_step_handler(message, self.edit_callback);
		elif message.text == self.remove_reply:
			self.bot.send_message(message.chat.id, "As you wish, but I will need track id");
			self.bot.register_next_step_handler(message, self.remove_callback);
		elif message.text == self.view_reply:
			self.view_music_collection(message);
	
	def subscribe_actions(self, call):
		params = call.data.split('_');
		if params[0] == "edit":
			track = self.music_library.get_by_id(params[1])
			self.edit_track(call.message, track["track_url"]);
		if params[0] == "plus":
			self.bot.send_message(call.message.chat.id, "to do");
		if params[0] == "minus":
			self.bot.send_message(call.message.chat.id, "to do");

	def command_handler(self, command, message):
		if command == "start":
			self.bot.send_message(message.chat.id, "Greetings stanger. I'm here to help you share music with your friends. Let's begin then, shall we?");

	def view_music_collection(self, message):
		for row in self.music_library.view_tracks({ "is_used": False}):
			menu = telebot.types.InlineKeyboardMarkup();
			menu.add(telebot.types.InlineKeyboardButton(text="Edit", callback_data="edit_"+ row["track_id"]));
			self.bot.send_message(message.chat.id, "Track: {0}\nFrom artist: {1}\nLink to listen: {2}\nDescription: {3}".format(row["track_id"], row["artist"], row["track_url"], row["description"]), reply_markup=menu);

	def insert_callback(self, message):
		music_track = MusicTrack();
		music_track.add_link(message.text); 
		self.bot.send_message(message.chat.id, "Great! Tell me, who is the artist?");
		self.bot.register_next_step_handler(message, self.artist_input_handler, music_track);

	def artist_input_handler(self, message, music_track):
		music_track.artist = message.text;
		self.bot.send_message(message.chat.id, "And finally, come up with a description (genre, artist and background)");
		self.bot.register_next_step_handler(message, self.description_input_handler, music_track);

	def description_input_handler(self, message, music_track):
		music_track.description = message.text;
		music_track.save();
		self.bot.send_message(message.chat.id, "Done! Track added to collection");

	def remove_callback(self,message):
		self.music_library.delete_track(message.text);
		self.bot.send_message(message.chat.id, "Track removed from collection");

	def edit_callback(self, message):
		edit_track(message, message.text);

	def edit_track(self, message, track_url):
		self.bot.send_message(message.chat.id, "Ok, now enter a new description");
		self.bot.register_next_step_handler(message, self.save_edited_data, track_url);

	def save_edited_data(self, message, track_id):
		self.music_library.edit_track({"track_url": track_id}, {'description': message.text});

	def get_creator_menu(self):
		menu = telebot.types.ReplyKeyboardMarkup();
		menu.row(self.insert_reply);
		menu.row(self.edit_reply);
		menu.row(self.remove_reply);
		menu.row(self.view_reply);
		return menu;

class UserResponder(Responder):
	NEW_TRACK_STARTERS = ["Дай ка подумаю...🤔", "Ага, что тут у нас", "Предлагаю твоему вниманию", "Этот мне очень нравиться🤩", "Начнем с этого", "Уфф, готовся!", "Создатель постарался, конечно👍", "Для такой девушки ничего не жалко!💖"];
	NEW_TRACK_IMPRESSIONS = ["Как тебе?", "Расскажи о своих впечетлениях", "Буду ждать твоих впечетлений", "Что думаешь?", "Не забудь прокомментировать", "Вижу ведь, что понравилось!"];

	music_library = MusicLibrary();
	chats_info = ChatsInfo();

	def __init__(self, bot):
		self.bot = bot
		super().__init__(bot)

	def respond(self, message):
		sentence = message.text;
		#success, respond = self.check_for_greeting(sentence);
		if any(word in message.text.lower() for word in ["music", "track", "techno", "new one", "listen", "🎶", "🎵" ]):
			last_track = self.chats_info.get_last_track(LOVER_USER_ID);
			track = self.music_library.get_new_track(last_track);
			self.send_music_track(message, track);
		elif any(word in message.text.lower() for word in ["thx", "thanks"]):
			self.bot.send_message(message.chat.id, "You're welcome");
	def subscribe_actions(self, call):
		params = call.data.split('_');
		if params[0] == "imp":
			self.bot.send_message(call.message.chat.id, random.choice(["Recording🎙", "I’m listening to you🎧", "Go for it", "Listening you carefully🎧"]));
			self.bot.register_next_step_handler(call.message, self.impression_input, params[1]);
		elif params[0] == "artist":
			self.bot.send_message(call.message.chat.id, random.choice(["Ага, поищем..", "Дай ка подумать", "Милисекундочку"]));
			track = self.music_library.get_by_artist(params[1]);
			if track == None:
				self.bot.send_message(call.message.chat.id, "Увы, больше трэков от {0} нет...Но я передам Тимофею и когда он добавит ты об этом неприменно узнаешь😉".format(params[1]));
				self.bot.send_message(call.message.chat.id, "А пока могу предложить тебе что-то другое");
				self.send_music_track(call.message, self.music_library.get_new_track());
				self.bot.send_message(self.chats_info.get_chat_id("timothy_y"), "Alert🚨🚨🚨\nДорогая Настя хочет еще музыки от {0}. Тебе стоит заняться этим!".format(params[1]));
			self.send_music_track(call.message, track);

	def send_music_track(self, message, track):
		if track == None:
			self.bot.send_message(message.chat.id, "😢😢😢");
			self.bot.send_message(message.chat.id, "Извини {0}, но новый музыки пока нет. Я передам Тимофею и когда он добавт ты об этом неприменно узнаешь😉".format(random.choice(self.NICKNAMES)));
			self.bot.send_message(self.chats_info.get_chat_id("timothy_y"), "Alert🚨🚨🚨\nЗакончилась музыка для любимой Насти. Тебе стоит заняться этим!");
		else:
			self.chats_info.set_last_track(LOVER_USER_ID, track["track_id"]);
			self.bot.send_message(message.chat.id, random.choice(self.NEW_TRACK_STARTERS));
			track_menu = telebot.types.InlineKeyboardMarkup();
			track_menu.add(telebot.types.InlineKeyboardButton(text="Apple Music🎵", url=track["track_url"]));
			self.bot.send_message(message.chat.id, "#MusicFromTimothy\n" + track["track_id"].replace("-", " ").title() + random.choice([" от ", " - ", " в исполнении "]) + "#" + track["artist"],reply_markup=track_menu);
			#self.bot.send_message(message.chat.id, "Ссылка на прослушивание:\n{0}".format(track["track_url"]));
			if track["description"] != "-": self.bot.send_message(message.chat.id, track["description"]);
			impressions = telebot.types.InlineKeyboardMarkup();
			impressions.add(telebot.types.InlineKeyboardButton(text="Рассказать впечетления", callback_data="imp_"+ track["track_id"]));
			impressions.add(telebot.types.InlineKeyboardButton(text="Еще от {0}".format(track["artist"]), callback_data="artist_" + track["artist"]));
			self.bot.send_message(message.chat.id, random.choice(self.NEW_TRACK_IMPRESSIONS), reply_markup=impressions)

	def check_for_greeting(self, sentence):
		for word in sentence.words:
			if word.lower() in GREETING_KEYWORDS:
				return True, "Приветсвую тебя, Настя. Да - я знаю, кто ты. Создатель запрограмировал меня определять тебя из миллиардов людей."
		return False, '';
	
	def impression_input(self, message, track_id):
		self.music_library.rate_track(track_id, message.text);
		self.send_feedback(message.text, track_id)
		self.bot.send_message(message.chat.id, random.choice(["Спасибо😘", "Лестно", "Передам", "Красиво сказано!😍", "Рад, что тебе понравилось😉"]));

	def send_feedback(self, comment, track_id):
		creator_chat_id = self.chats_info.get_chat_id("timothy_y");
		self.bot.send_message(creator_chat_id, "#NastiaImpressions\nНаша любимая Настя прослушала и оценила трэк {0}".format(track_id.replace("-", " ").title()));
		self.bot.send_message(creator_chat_id, "Цитирую:\n{0}".format(comment));

	def get_lover_menu(self):
		menu = telebot.types.ReplyKeyboardMarkup();
		menu.row("Попросить музыку🎵");
		return menu;

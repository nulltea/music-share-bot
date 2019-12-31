import telebot

from responders import *;
from config import *;
from data_storage import ChatsInfo;


class MusicBot:
	def __init__(self):
		self.bot = telebot.TeleBot(TOKEN);
		self.chats_info = ChatsInfo();
		super().__init__();

	def initialize(self):
		self.user_input_handler();
		self.subscribe_actions();
		self.user_commnads_handler();

	def get_responder(self, chat):
		if chat.username == CREATOR_USER_ID:
			return Responder(self.bot);
		elif chat.username == LOVER_USER_ID:
			return LoverResponder(self.bot);
		elif chat.username == FRIEND_USER_ID:
			return FriendResponder(self.bot);
		else:
			return Responder(self.bot);

	def activate_bot(self):
		self.bot.polling();

	def text_to_love(self, message):
		self.bot.send_message(self.chats_info.get_chat_id(LOVER_USER_ID), message);

	def user_input_handler(self):
		@self.bot.message_handler(content_types=["text"])
		def send_text(message):
			self.chats_info.upsert_chat({"username": message.chat.username, "chat_id": message.chat.id});
			responder = self.get_responder(message.chat);
			responder.respond(message);

	def subscribe_actions(self):
		@self.bot.callback_query_handler(func=lambda call: True)
		def callback_worker(call):
			responder = self.get_responder(call.message.chat);
			responder.subscribe_actions(call);

	def user_commnads_handler(self):
		@self.bot.message_handler(commands=["start"])
		def start_message(message):
			responder = self.get_responder(message.chat);
			responder.command_handler("start", message)

		@self.bot.message_handler(commands=["help"])
		def start_message(message):
			responder = self.get_responder(message.chat);
			responder.command_handler("help", message)

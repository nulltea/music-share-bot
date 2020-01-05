import telegram as tg;
import telebot;

from responders import *;
from config import *;
from data_storage import BotUser;


class MusicBot:
	def __init__(self):
		self.bot = telebot.TeleBot(TOKEN);
		self.responder = Responder(self.bot);
		super().__init__();

	def initialize(self):
		self.responder.init_action_dictionary();
		self.user_input_handler();
		self.subscribe_actions();
		self.user_commnads_handler();

	def activate_bot(self):
		self.bot.polling();

	def user_input_handler(self):
		@self.bot.message_handler(content_types=["text"])
		def send_text(message):
			self.responder.respond(message);

	def subscribe_actions(self):
		@self.bot.callback_query_handler(func=lambda call: True)
		def callback_worker(call):
			self.responder.subscribe_actions(call);

	def user_commnads_handler(self):
		@self.bot.message_handler(commands=["start"])
		def start_message(message):
			self.responder.command_handler("start", message)

		@self.bot.message_handler(commands=["help"])
		def start_message(message):
			self.responder.command_handler("help", message)

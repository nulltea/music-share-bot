import telebot;
from config import *;
from responders import *;


class MusicBot:
	def __init__(self):
		self.bot = telebot.TeleBot(config["telegram"]["token"]);
		self.responder = Responder(self.bot);
		super().__init__();

	def initialize(self):
		self.responder.init_action_dictionary();
		self.user_commands_handler();
		self.user_input_handler();
		self.subscribe_actions();

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

	def user_commands_handler(self):
		@self.bot.message_handler(commands=["start", "help", "menu", "add", "view", "get"])
		def start_message(message):
			self.responder.command_handler(message.text.lstrip("/"), message)

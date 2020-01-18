import configparser;
import io;
from collections import defaultdict;


MUSIC_GENRES = ["Alternative", "Electronic", "Techno", "Hip-Hop", "Pop", "R&B", "Rock", "Metal", "Classical", "Country", "Reggae", "Indie"]


def tree():
	return defaultdict(tree)


def read_config():
	configreader = configparser.ConfigParser();
	configreader.read("config.ini");
	config = tree();
	for section in configreader.sections():
		for option in configreader.options(section):
			config[section][option] = configreader.get(section, option);
	return config;


config = read_config();

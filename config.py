import configparser;
from collections import defaultdict;


MUSIC_GENRES = ["Alternative", "Electronic", "Techno", "Hip-Hop", "Pop", "R&B", "Rock", "Metal", "Classical", "Country", "Reggae", "Indie"]


def tree():
	return defaultdict(tree)


def read_config():
	configreader = configparser.ConfigParser();
	configreader.read("config.ini");
	config_dict = tree();
	for section in configreader.sections():
		for option in configreader.options(section):
			config_dict[section][option] = configreader.get(section, option);
	return config_dict;


config = read_config();

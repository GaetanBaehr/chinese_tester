from collections import defaultdict
import random
import csv
import requests
import string
import unicodedata


def format_dictionary_todict(teamRows):
	dictionary = []
	for element in teamRows:
		word, pronunciation, translation = element
		dictionary.append(
			dict(
			word = word.split(" / "),
			pronunciation = pronunciation.split(" / "),
			translation = translation.split(" / "),
			)
		)
	return dictionary


def get_dictionary(spreadsheetURL=None):
	if spreadsheetURL is None:
		spreadsheetURL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSu9lE7IWNrwypkuhQ2MmtGmfImmVVHW57GG4dE8ij5lP06SRhPPIHq5G5w_8NdIgN9-voL4kEMwzYS/pub?gid=520398043&single=true&output=csv"

	response = requests.get(spreadsheetURL)
	data = response.content
	dictionary = list(csv.reader(data.decode("utf-8").splitlines()))

	return format_dictionary_todict(dictionary)


def pop_accent(character):
	composition = unicodedata.decomposition(character).split()
	for comp in composition:
		char = chr(int(comp,16))
		if char in string.ascii_letters:
			return char
	return character


def sanitize_string(string, removeAccent = True):
	elements_to_remove = [" ", "\n", "\t"]
	for elem in elements_to_remove:
		string = string.replace(elem, "")
	string.lower()
	if removeAccent:
		ns = ""
		for char in string:
			ns += pop_accent(char)
		return ns
	return string


def sanitize_element(element):
	if isinstance(element, list):
		return [sanitize_string(e) for e in element]
	elif isinstance(element, str):
		return sanitize_string(element)
	else:
		return element


class Controller:


	selection_rule = .25


	def __init__(self):
		self.retention = 10
		self.recently_seen = []


	def instanciate_data(self, dictionary):
		self.dictionary = dictionary
		self.word_2_pronunciation = {}
		self.pronunciation_2_word = defaultdict(list)
		self.translation_2_word = defaultdict(list)
		self.word_2_translation = defaultdict(list)
		self.all_chars = set()
		for elem in dictionary:
			pronunciation = elem.get("pronunciation")
			translation = elem.get("translation")
			word = elem.get("word")
			for w in word:
				for x in w: self.all_chars.add(x)
			for i, c in enumerate(word):
				self.word_2_pronunciation[c] = pronunciation[i]
				self.word_2_translation[c].extend(translation)
			for t in translation:
				self.translation_2_word[t].extend(word)
		for k, v in self.word_2_pronunciation.items():
			self.pronunciation_2_word[v].append(k)


	def _add_item(self, index):
		if len(self.recently_seen) >= self.retention:
			self.recently_seen.pop(0)
		self.recently_seen.append(index)


	def _select_item(self):
		lenght = len(self.dictionary)
		range = int(lenght * self.selection_rule)
		selected_list = random.choice([
			self.dictionary[:-range], 
			self.dictionary[-range-1:]
			])
		return random.choice(
			selected_list
			)


	def select_item(self, mode = 'random'):
		def _get_item(self):
			selected_item = self._select_item()
			index = self.dictionary.index(selected_item)
			return index, selected_item
		index, selected_item = _get_item(self)
		while index in self.recently_seen:
			index, selected_item = _get_item(self)

		if mode == 'random':
			self.selected_category = random.choice(
				list(selected_item.keys())
				)
		else:
			self.selected_category = mode
		self.selected_question = random.choice(
			selected_item[self.selected_category]
			)
		if self.selected_category == "word":
			word = self.selected_question
			translation = self.word_2_translation[self.selected_question]
		elif self.selected_category == "pronunciation":
			word = self.pronunciation_2_word[self.selected_question]
			translation = [x for w in word for x in self.word_2_translation[w]]
		else:
			translation = self.selected_question
			word = self.translation_2_word.get(translation)
		self.answer = dict(word = word, translation = translation)
		self._add_item(index)


	def _reformatstring(self, e):
		return [
			e,
			e.replace(" ", ""),
			e.lower()
		]


	def verify_answer(self, word = "", pronunciation = "", translation = ""):
		if self.selected_category == "pronunciation":
			anwserwords = sanitize_element(self.answer["word"])
			answertranslation = sanitize_element(self.answer["translation"][self.answer["word"].index(word)])
			if word in anwserwords and translation == answertranslation:
				return True
		elif self.selected_category == "word":
			for p in self._reformatstring(pronunciation):
				if p == sanitize_element(self.word_2_pronunciation[word]) and translation in sanitize_element(self.word_2_translation[word]):
					return True
		else:
			for p in self._reformatstring(pronunciation):
				if word in sanitize_element(self.translation_2_word[translation]) and p == sanitize_element(self.word_2_pronunciation[word]):
					return True
		return False


	def input_answer(self, text):
		value = input(text)
		if value == "help":
			print("".join(sorted(list(self.all_chars))))
			self.input_answer(text)
		return value


def contest(controller, round = 20, mode = 'random'):
	print("\n")
	count = 0
	for i in range(round):

		controller.select_item(mode)
		
		print(f"{str(i+1).zfill(len(str(round)))}/{round}: {controller.selected_category} is:", controller.selected_question)
		
		if controller.selected_category == "pronunciation":
			pronunciation = controller.selected_question
			word = controller.input_answer("\t• word: ")
			translation = controller.input_answer('\t• translation: ')
		elif controller.selected_category == "word":
			word = controller.selected_question
			pronunciation = controller.input_answer("\t• pronunciation: ")
			translation = controller.input_answer('\t• translation: ')
		else:
			translation = controller.selected_question
			word = controller.input_answer("\t• word: ")
			pronunciation = controller.input_answer("\t• pronunciation: ")


		result = controller.verify_answer(
			word = sanitize_element(word), 
			pronunciation = sanitize_element(pronunciation), 
			translation = sanitize_element(translation)
			)

		if not result:
			answer = dict(controller.answer)
			if isinstance(answer["word"], list):
				word = answer["word"][0]
			else: word = answer["word"]
			answer["pronunciation"] = controller.word_2_pronunciation[word]
			answer_string = ''
			for k, v in answer.items():
				answer_string += f"{k}: {' '.join(v) if isinstance(v,list) else v}, "
			print("💥💥💥", result, "answer:", answer_string, "\n")
		else:
			print("🎉🎉🎉", result, "\n")
			count += 1

	print(f"End, score={str(count).zfill(len(str(round)))}/{round}\n")
	restart = input("restart? y / n:\n")
	if restart == "y":
		contest(controller, round, mode)


def convert_to_int(e):
	if isinstance(e, (int, float)):
		return int(e)
	elif isinstance(e, str):
		try:
			return int(e)
		except: return False
	return False


if __name__ == "__main__":
	controller = Controller()
	dictionary = get_dictionary()
	controller.instanciate_data(dictionary)
	number_of_round = convert_to_int(input("How many round? "))
	assert number_of_round
	print("\nmode:\n    1-random\n    2-word\n    3-pronunciation\n    4-translation")
	m = convert_to_int(input("give index: "))
	print("\n")
	assert m in [1, 2, 3, 4]
	mode = ["random", "word", 'pronunciation', "translation"][m-1]

	start_settings = input("start or settings: ")
	assert start_settings in ["start", "settings"]
	if start_settings == "start":
		print("\n--------------------------")
		print("        Here we go")
		print("--------------------------")

		contest(controller, round = int(number_of_round), mode = mode)

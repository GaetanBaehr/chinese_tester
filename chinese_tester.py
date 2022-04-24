from collections import defaultdict
import random
import csv
import requests


spreadsheetURL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSu9lE7IWNrwypkuhQ2MmtGmfImmVVHW57GG4dE8ij5lP06SRhPPIHq5G5w_8NdIgN9-voL4kEMwzYS/pub?gid=520398043&single=true&output=csv"
response = requests.get(spreadsheetURL)
data = response.content
teamRows = list(csv.reader(data.decode("utf-8").splitlines()))

def format_teamRows_todict(teamRows):
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

dictionary = format_teamRows_todict(teamRows)

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
		for elem in dictionary:
			pronunciation = elem.get("pronunciation")
			translation = elem.get("translation")
			word = elem.get("word")
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


	def select_item(self):
		def _get_item(self):
			selected_item = self._select_item()
			index = self.dictionary.index(selected_item)
			return index, selected_item
		index, selected_item = _get_item(self)
		while index in self.recently_seen:
			index, selected_item = _get_item(self)

		self.selected_category = random.choice(
			list(selected_item.keys())
			)
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
			if word in self.answer["word"] and translation == self.answer["translation"][self.answer["word"].index(word)]:
				return True
		elif self.selected_category == "word":
			for p in self._reformatstring(pronunciation):
				if p == self.word_2_pronunciation[word] and translation in self.word_2_translation[word]:
					return True
		else:
			for p in self._reformatstring(pronunciation):
				if word in self.translation_2_word[translation] and p == self.word_2_pronunciation[word]:
					return True
		return False


def contest(controller, round = 20):
	count = 0
	for i in range(round):

		controller.select_item()
		
		print(f"{str(i+1).zfill(len(str(round)))}/{round}: {controller.selected_category} is:", controller.selected_question)
		
		if controller.selected_category == "pronunciation":
			pronunciation = controller.selected_question
			word = input("\t• word ")
			translation = input('\t• translation: ')
		elif controller.selected_category == "word":
			word = controller.selected_question
			pronunciation = input("\t• pronunciation: ")
			translation = input('\t• translation: ')
		else:
			translation = controller.selected_question
			word = input("\t• word: ")
			pronunciation = input("\t• pronunciation: ")

		result = controller.verify_answer(
			word = word, 
			pronunciation = pronunciation, 
			translation = translation
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

	print(f"End, score={str(count).zfill(len(str(round)))}/{round}")



if __name__ == "__main__":
	controller = Controller()
	controller.instanciate_data(dictionary)

	contest(controller, round = 5)
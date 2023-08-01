import csv
from collections import Counter

def find_ngrams(w, n):

  		return ["".join(seq) for seq in zip(*[w[i:] for i in range(n)])]
  		
def get_all_ngrams(words, n=5):


  
	"""
	extract all ngrams from a list of words.
	n: the maximum length of an n-gram.
	return: a list of tuples (ngram, freq), sorted according to the frequency.
	"""

	fc = Counter()

	for w in words:
 
 		ngrams = []
 		for k in range(1, min(n+1, len(w)+1)):
   			ngrams = ngrams + find_ngrams(w, k)

 		fc.update(ngrams)

	
	items = fc.items()
	
	return fc
	

def get_verb_suffixes(words, verbs = True):

	suffixes = []
	
	for w in words:
	
		if "!" in w:
			w, suffix = w.split("!")
			if suffix:
				if verbs:
					suffixes.append(suffix)
				else:
					for c in suffix:
						suffixes.append(c)
	
	return set(suffixes)
	
	
def read_words(filename):
	
	words = []
	with open(filename, "r") as f:
		lines = f.readlines()

	for line in lines:

		w = line.strip()
		words.append(w)

	return words
	

def generate_index_mapping(words, include_special_tokens = True):
	if include_special_tokens:
		if "<unk>" not in words: words = ["<unk>"] + words
		if "<begin>" not in words: words = ["<begin>"] + words
		if "<end>" not in words: words = ["<end>"] + words
		if "<verb>" not in words: words = ["<verb>"] + words
		words = ["<sg>"] +  words 
		words = ["<pl>"] + words
		words = ["<amb>"] + words

	tokens = words
	
	W2I = {w:i for i,w in enumerate(tokens)}
	I2W = {i:w for i,w in enumerate(tokens)}
	return W2I, I2W
	
def create_dataset(filename):


	dataset = []
	analyser_outputs = set()

	with open(filename, "r") as f:

		reader = csv.reader(f)

		for i, row in enumerate(reader):

			sent_dictionary = {}
			
			if i == 0:
			
				keys = row
				
			else:
			
				for j, val in enumerate(row):
					sent_dictionary[keys[j]] = val

				dataset.append(sent_dictionary)
	
	return dataset


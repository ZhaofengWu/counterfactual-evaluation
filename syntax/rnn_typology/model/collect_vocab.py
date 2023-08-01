#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Counter
import csv
import numpy as np
import io
import argparse


VOC_SIZE = 200000
NGRAM_SIZE = 100000

def read_words():
	"""
	extreact all words from the csv file that contains the data sentences.
	return: a list of tuples (word, frequency), sorted according to the frequency (highest first).
	"""

	counter = Counter()

	with open("../datasets/deps_train.csv", "r") as f:
	
		reader = csv.reader(f)
		data = []
		
		for i, row in enumerate(reader):
			sent_dict = {}

			
			if i == 0:
			
				keys = row

			else:

				for j, element in enumerate(row):
					sent_dict[keys[j]] = element
			
				sent, sent_pos = sent_dict['sent_words'].split(" "), sent_dict['sent_pos'].split(" ")
				for (w,pos) in zip(sent, sent_pos):
				
					counter[w] += 1


	return counter
	
	

def write_to_file(container, file_name, write_special_tokens = True):

	"""
	container: a list of strings
	write the items into a file.
	"""
	sep="\t"


	with open(file_name, "w") as f:
	
		if write_special_tokens:
			f.write(("<unk>"+sep+str(1)+"\n"))
			f.write(("<begin>"+sep+str(1)+"\n"))
			f.write(("<end>"+sep+str(1)+"\n"))
			f.write(("<verb>"+sep+str(1)+"\n"))
			
		for w in container:
			if w!=" ":

				f.write(w+"\n")

words_and_freqs = read_words().most_common(VOC_SIZE)
words =[w for (w,f) in words_and_freqs]
write_to_file(words, "words.txt")

from utils import get_all_ngrams
ngrams_and_freqs = get_all_ngrams(words).most_common(NGRAM_SIZE)
ngrams = [n for (n,f) in ngrams_and_freqs]
write_to_file(ngrams, "ngrams.txt")

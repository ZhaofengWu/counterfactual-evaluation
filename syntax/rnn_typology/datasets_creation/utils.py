from collections import Counter
import csv
import subprocess


def get_all_ngrams(words, n=5):

	def find_ngrams(w, n):
  		return ["".join(seq) for seq in zip(*[w[i:] for i in range(n)])]
  
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
	
	
def read(fname):
	p = subprocess.Popen(['gunzip', '-c', fname], stdout=subprocess.PIPE)
	for line in p.stdout:
		yield line
	p.wait()
		

def tokenize(fh):
	sent = []
	for line in fh:
		line = line.strip().split()
		if not line:
			if sent:
				yield sent
			sent = []
		else:
			sent.append(line)
	yield sent


def write_to_csv(sents, fname = "deps.csv", mode = "w"):

	with open("../datasets/"+fname, mode) as f:
		
		writer = csv.writer(f, delimiter=',')
		
		for s in sents:
		
			writer.writerow(s)

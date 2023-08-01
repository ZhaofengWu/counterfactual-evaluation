from subprocess import call
import time

from utils import *
from encoder import *
from rnn import *
from data_generator import *
from get_datasets import *
import dynet as dy
from embedding_collector import *
from prediction_recorder import *



if __name__ == "__main__":

	
	model = dy.Model()
	dg = NumberPredictionGenerator(TRAIN, DEV, TEST, NUMBER2I)
	encoder = CompleteSubwordEncoder(model, W2I, NGRAM2I)
	collector = Collector(encoder, "words_and_pos.txt", "embeddings.txt")
	recorder = PredictionRecorder()
	agreemets = ["nsubj", "dobj", "iobj"]
	rnn = RNN(model, encoder, dg, I2NUMBER, collector, recorder, agreements = agreemets)
	rnn.train(epochs = 1)
	d = rnn.evaluate(mode = "test")


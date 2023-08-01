import csv

import dynet as dy
import numpy as np
from collections import Counter

from encoder import EMBEDDING_SIZE
LSTM_HIDDENSIZE = 150
NUM_LAYERS = 1
PREDICTION_HIDDEN_LAYERS = [LSTM_HIDDENSIZE, 100, 50, 3]
RNN_DROPOUT = 0.1
ATTENTION = False
ATTENTION_SEPERATE = False

class RNN(object):

	def __init__(self, model, encoder, data_generator, I2NUMBER, collector, recorder, agreements = ["nsubj", "dobj", "iobj"]):
	
		self.agreements = agreements
		self.model = model
		self.encoder = encoder
		self.generator = data_generator
		self.I2NUMBER = I2NUMBER
		self.collector = collector
		self.recorder = recorder
		
		self.create_model()
	
	def create_model(self):

     
		self.biLSTM_fwd = dy.LSTMBuilder(NUM_LAYERS, EMBEDDING_SIZE, LSTM_HIDDENSIZE, self.model)
        	self.biLSTM_bwd = dy.LSTMBuilder(NUM_LAYERS, EMBEDDING_SIZE, LSTM_HIDDENSIZE, self.model)
        	self.W_combine = self.model.add_parameters((LSTM_HIDDENSIZE, 2*LSTM_HIDDENSIZE))
        	self.W_attention_simple = self.model.add_parameters((1, LSTM_HIDDENSIZE))
		self.W_attention_simple2 = self.model.add_parameters((1, LSTM_HIDDENSIZE))
		self.W_attention_simple3 = self.model.add_parameters((1, LSTM_HIDDENSIZE))
		self.prediction_weights = []
		
		for arg in self.agreements:
		
			arg_params = []
			
			for (in_size, out_size) in zip(PREDICTION_HIDDEN_LAYERS, PREDICTION_HIDDEN_LAYERS[1:]):
	
        			W = self.model.add_parameters((out_size, in_size))
        			b = self.model.add_parameters((out_size, 1))
        			arg_params.append((W,b))
        			
        		self.prediction_weights.append(arg_params)

        	self.trainer = dy.AdamTrainer(self.model)
		self.trainer.set_clip_threshold(1.0)	
	
		
	def _predict(self, sentence, training = True):    

		if training:
		
			self.biLSTM_fwd.set_dropout(RNN_DROPOUT)
			self.biLSTM_bwd.set_dropout(RNN_DROPOUT)
		else:
			self.biLSTM_fwd.set_dropout(0.)
			self.biLSTM_bwd.set_dropout(0.)
			
		#prepare parameters

		s_fwd = self.biLSTM_fwd.initial_state()
		s_bwd = self.biLSTM_bwd.initial_state()
     		W_combine = dy.parameter(self.W_combine)
     		
		# encode sentence & pass through biLstm

		encoded = [self.encoder.encode(w) for w in sentence]
		verb_index = sentence.index("<verb>")
		output_states_fwd = s_fwd.transduce(encoded)
		output_states_bwd = s_bwd.transduce(encoded[::-1])

		outputs = [fwd+bwd for (fwd,bwd) in zip(output_states_fwd,output_states_bwd[::-1])]
		
		o = outputs[verb_index]
			
		preds = []
	
		for i, agr in enumerate(self.agreements):

			h = o
				
			for k, (w, b) in enumerate(self.prediction_weights[i]):
		
				w_param, b_param = dy.parameter(w), dy.parameter(b)
				h = w_param * h + b_param
				
				if k != len(self.prediction_weights[i]) - 1:
					
					h = dy.rectify(h)
			
			preds.append(h)
        
		return preds
        
	def train(self, epochs=30):
	
		n = self.generator.get_train_size()
		print "size of training set: ", n
          	print "Training..."
          	
		iteration = 0
		losses = []
		loss_avg = 0.
		
		for i, batch in enumerate(self.generator.generate(mode="train")):

			dy.renew_cg()
					
				
			for j, training_example in enumerate(batch):

				x, y, data_sample = training_example
				preds = self._predict(x, training = True)
			
				loss = dy.scalarInput(0.)
			
				for agr,pred in zip(self.agreements, preds):
				
					true_number = y[agr]
					loss += dy.pickneglogsoftmax(pred, true_number)
				
				losses.append(loss)
					
				if iteration % n % 2500 == 0:
					print "{}/{}".format(iteration%n,n)
			
				iteration += 1
			
				#stopping criteria
	
				if iteration > epochs*n: 
			
					return
				
				# report progress. 

				if iteration%n == 0:

					print "EPOCH {} / {}".format(iteration/n, epochs)
					print "Average loss: {}".format(loss_avg / n)
					loss_avg = 0.
					self.evaluate(mode = "dev")
					#self.collector.collect()
					losses = []

			if losses:
			
				loss_sum = dy.esum(losses)
				loss_sum.forward()
				loss_sum.backward()
				self.trainer.update()
				loss_avg += loss_sum.value()
				losses = []


	def evaluate(self, mode = "dev"):
	
		
		n = self.generator.get_dev_size() if mode == "dev" else self.generator.get_test_size()

          	print "Evaluating..."
          	good = Counter()
          	bad = Counter()
          	total = Counter()
          	total_good = Counter()
          	total_bad = Counter()
          	
          	good = Counter()
          	bad = Counter()
          	total = Counter()
          	total_good = Counter()
          	total_bad = Counter()
          	
		iteration = 0
		good_o, bad_o, good_s, bad_s, good_i, bad_i = 1., 1., 1., 1., 1., 1.
		losses = []
		loss_avg = 0.
		index = 0
		
		for i, batch in enumerate(self.generator.generate(mode = mode)):

			dy.renew_cg()
						
			for j, training_example in enumerate(batch):

				index += 1
				
				predictions_correct = {"nsubj": False, "dobj": False}
					
				x, y, data_sample = training_example
				is_transitive = self.I2NUMBER[y['dobj']] != "-"

				preds = self._predict(x, training = False)
				
				all_correct = True
				predictions = {}
				d = {}
				
				
				for agr,pred in zip(self.agreements, preds):
				
				
					true_number = y[agr]
					prediction = np.argmax(dy.softmax(pred).npvalue())
					predictions[agr] = self.I2NUMBER[prediction]
					
					is_ergative = is_transitive and agr == "nsubj"
					is_absolutive = agr == "dobj" or (agr == "nsubj" and not is_transitive)
					
			
					if self.I2NUMBER[y[agr]] != "-":
					
						total[agr] += 1
						if is_absolutive:
							total["abs"] += 1
						elif is_ergative:
							total["erg"] += 1
							
						if self.I2NUMBER[prediction] != "-":
							
							total_good[agr] += 1
							
							if is_absolutive:
								total_good["abs"] += 1
							elif is_ergative:
								total_good["erg"] += 1
						else:
							total_bad[agr] += 1
							
							if is_absolutive:
								total_bad["abs"] += 1
							
							elif is_ergative:
								total_bad["erg"] += 1
							
						
					if prediction == true_number:
					
						good[agr] += 1
						predictions_correct[agr] = True
						
						if is_absolutive:
						
							good["abs"] += 1
						elif is_ergative:
						
							good["erg"] += 1
					else:
						bad[agr] += 1
						all_correct = False
						
						if is_absolutive:
							bad["abs"] += 1
						elif is_ergative:
						
							bad["erg"] += 1				
					
				if index == n:
					
					
					for agr in self.agreements:
					
						
						acc = (1.*good[agr])/(bad[agr] + good[agr])
						recall = (1.*total_good[agr])/(total[agr])
		
						s =  "{}-accuracy {}\t{}-recall {}\t{}-number-of-instances {}".format(agr, acc, agr, recall, agr, total[agr])
						d[agr] = s
						print s
					return	d		
				

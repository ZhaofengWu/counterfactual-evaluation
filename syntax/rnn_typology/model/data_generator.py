import random

class DataGenerator(object):

	def __init__(self, train, dev, test):
		
		self.train = train
		self.dev = dev
		self.test = test
		
	def get_train_size(self):
		return len(self.train)
		
	def get_dev_size(self):
		return len(self.dev)
		
	def get_test_size(self):
		return len(self.test)
		
	def collect_existing_labels(self):
	
		pass 
	
	
	def generate(self, mode = "dev", random_choice = True):
	
		batch_size = 128
		i = 0
		
		while True: 
		

			batch = []
			source = self.train if mode == "train" else self.dev if mode == "dev" else self.test
			n = len(source)
			
			for k in range(batch_size):
			
				data_dict = source[i%n] if (not random_choice or not mode == "train") else random.choice(source)
		
				x,y = self.create_example(data_dict)
				batch.append((x,y, data_dict))
				
				i += 1
				
			yield batch
	
	def create_example(self, data):
	
	
		raise NotImplementedError
		
		
		
class NumberPredictionGenerator(DataGenerator):

	def __init__(self, train, dev, test, NUMBER2I):
	
		DataGenerator.__init__(self, train, dev, test)
		self.NUMBER2I = NUMBER2I
		
	def create_example(self, data_dict):	
	
		x = data_dict['sent_words'].split()
		verb_index = int(data_dict['verb_index'])
		x[verb_index] = "<verb>"
		
		arguments_numbers = {}
		
		for arg in ["nsubj", "dobj", "iobj"]:
		
			num = data_dict[arg+ "_number"]
			
			argument_number = self.NUMBER2I[num]
			arguments_numbers[arg] = argument_number
			
		y = arguments_numbers
		
		return x,y
		

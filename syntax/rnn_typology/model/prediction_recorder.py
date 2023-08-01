import csv

class PredictionRecorder(object):

	def __init__(self): 
	
		preds = []

	def add(self, data_dict, prediction, true):
	
		self.preds.append((data_dict, prediction, prediction == true))
	
	def write_to_file(self):
	
		keys = preds[0][0].keys()
		with open("preds.csv", "w") as f:
		
			writer = csv.writer(f, delimiter=',')
			writer.writerow(keys + ["prediction", "true"])
			
			for data_dict, pred, true in self.preds:
			
				line = [data_dict[key] for key in keys] + [pred, true]
				writer.writerow(line)
				
		self.preds = []

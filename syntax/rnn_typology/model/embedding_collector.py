
class Collector(object):

	def __init__(self, encoder, voc_file, embedding_filename):
		self.encoder = encoder
		self.voc_file = voc_file
		self.embedding_filename = embedding_filename
		
	def collect(self, size = 15000):
	
		print ("collecting embedding...")
		
		with open(self.voc_file, "r") as f:
			lines = f.readlines()
			
		vecs = []
		
		for i, line in enumerate(lines[:size]):
			#print i, len(lines)
			#if i % 500 == 0:
				#print "collecting embedding, line {}/{}".format(i, size)
			word, pos = line.strip().split("\t")
			vec = self.encoder.encode(word).value()
			vecs.append((word,pos, vec))
		
		f = open(self.embedding_filename, "w")

		for (w,pos,v) in vecs:
			as_string = " ".join([str(round(float(val),5)) for val in v])
			f.write(w+"\t"+pos+"\t"+as_string+"\n")
		f.close()
				

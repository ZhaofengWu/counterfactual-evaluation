import dynet as dy
from utils import find_ngrams

EMBEDDING_SIZE = 100

"""the files contains various encoders than can encode a string word to a real vector"""

class EmbeddingEncoder(object):

    def __init__(self, inp_size, model, W2I):

        self.model = model
        self.W2I = W2I
        self.E = model.add_lookup_parameters((inp_size, EMBEDDING_SIZE))

    def encode(self, w):

        word_encoded = self.W2I[w] if w in self.W2I else self.W2I["<unk>"]
        #print "word_encoded:", word_encoded
        word_encoded = dy.lookup(self.E, word_encoded)
        return word_encoded


class LSTMEncoder(object):

    def __init__(self, inp_size, model, CHAR2I):

        self.model = model
        self.CHAR2I = CHAR2I

        self.E2 = model.add_lookup_parameters((inp_size, EMBEDDING_SIZE))
        self.builder = dy.LSTMBuilder(16, EMBEDDING_SIZE, EMBEDDING_SIZE, self.model)


    def encode(self, w):

        s = self.builder.initial_state()
        assert w!=""
        encoded = [self.CHAR2I[c] if c in self.CHAR2I else self.CHAR2I["<unk>"] for c in w]
        embedded = [dy.lookup(self.E2, char) for char in encoded]

        lstm_out = s.transduce(embedded)[-1]
        assert lstm_out is not None
        return lstm_out

class SubwordEncoder(object):

    def __init__(self, inp_size, model, W2I, S2I, P2I, OUTPUT2IND):

        self.model = model
        self.W2I = W2I
        self.S2I = S2I
        self.P2I = P2I
        self.OUTPUT2IND = OUTPUT2IND
        self.i = 0

        self.E = model.add_lookup_parameters((inp_size, EMBEDDING_SIZE))
        self.E_pre = self.model.add_lookup_parameters((len(P2I), EMBEDDING_SIZE))
        self.E_suf = self.model.add_lookup_parameters((len(S2I), EMBEDDING_SIZE))
        self.W = model.add_parameters((EMBEDDING_SIZE, EMBEDDING_SIZE*4))
        self.E_output = model.add_lookup_parameters((len(OUTPUT2IND), EMBEDDING_SIZE))

    def encode_old(self, w):
              self.i+=1
              pre3, suf3 = w[:3], w[-3:]
              pre3_idx =  self.P2I[pre3] if pre3 in self.P2I else self.P2I["<unk>"]            
              suf3_idx =  self.S2I[suf3] if suf3 in self.S2I else self.S2I["<unk>"]

              pre2, suf2 = w[:2], w[-2:]
              pre2_idx =  self.P2I[pre2] if pre2 in self.P2I else self.P2I["<unk>"]            
              suf2_idx =  self.S2I[suf2] if suf2 in self.S2I else self.S2I["<unk>"]

              word_encoded = self.W2I[w] if w in self.W2I else self.W2I["<unk>"]

              word_e = dy.lookup(self.E, word_encoded)
              pre2_e  = dy.lookup(self.E_pre, pre2_idx)
              suf2_e = dy.lookup(self.E_suf, suf2_idx)
              pre3_e  = dy.lookup(self.E_pre, pre3_idx)
              suf3_e = dy.lookup(self.E_suf, suf3_idx)

              W = dy.parameter(self.W)

              return W * dy.concatenate([word_e, pre2_e+pre3_e, suf2_e+suf3_e])
              #return W * dy.concatenate([suf2_e, suf3_e])

    def encode(self, w, o, s):

              k = 5

              suffixes, prefixes = [], []

              for i in range(1,k+1):

                pre, suf = w[:i], w[-i:]
                pre_idx = self.P2I[pre] if pre in self.P2I else self.P2I["<unk>"]            
                suf_idx = self.S2I[pre] if pre in self.S2I else self.S2I["<unk>"]            
                suf_e = dy.lookup(self.E_suf, suf_idx)
                pre_e = dy.lookup(self.E_pre, pre_idx)
                suffixes.append(suf_e)
                prefixes.append(pre_e)
        
              word_encoded = self.W2I[w] if w in self.W2I else self.W2I["<unk>"]
              word_e = dy.lookup(self.E, word_encoded)

              exp_out = dy.vecInput(EMBEDDING_SIZE)
              if o==[]: o=["<unk>"]
              for out_token in o:
                  out_token_encoded = self.OUTPUT2IND[out_token] if out_token in self.OUTPUT2IND else self.OUTPUT2IND["<unk>"]
              out_embedding = dy.lookup(self.E_output, out_token_encoded)
              exp_out = exp_out + out_embedding

              W = dy.parameter(self.W)

              return W * dy.concatenate([word_e, dy.esum(suffixes), dy.esum(prefixes), out_embedding])
              #return W * dy.concatenate([suf2_e, suf3_e])

class CompleteSubwordEncoder(object):

    def __init__(self, model, W2I, NGRAM2I):

        self.model = model
        self.NGRAM2I = NGRAM2I
        self.W2I = W2I

        self.E_w = model.add_lookup_parameters((len(W2I), EMBEDDING_SIZE))
        self.E_ngram = model.add_lookup_parameters((len(NGRAM2I), EMBEDDING_SIZE))

        self.W = model.add_parameters((EMBEDDING_SIZE, 2*EMBEDDING_SIZE))
        self.b = model.add_parameters((EMBEDDING_SIZE, 1))
        
    def _all_ngrams(self, w, k):
        ngrams = []
        for j in range(1, k):
            ngrams+=["".join(seq) for seq in zip(*[w[i:] for i in range(j)])]
        return ngrams

    def encode(self, w, include_ngrams = True, sum_embeddings=False, noramlize=False):
    
	#print w,o,l, len(self.OUTPUT2IND), len(self.E_w) , len(self.E_ngram) , len(self.E_output)
	
        # word embedding

        w_encoded = self.W2I[w] if w in self.W2I else self.W2I["<unk>"]
        w_embedding = dy.lookup(self.E_w, w_encoded)
	#print "word {} is known: {}".format(w, w in self.W2I)
        # ngrams embeddings
        #ngrams = [ngram for ngram in ngrams if (ngram!=w or len(w)==1)]
        ngrams = self._all_ngrams(w, 5)
        ngrams_embedding = dy.vecInput(EMBEDDING_SIZE)
	
        for ngram in ngrams:

            ngram_encoded = self.NGRAM2I[ngram] if ngram in self.NGRAM2I else self.NGRAM2I["<unk>"]
            ngram_e = dy.lookup(self.E_ngram, ngram_encoded)    
            if include_ngrams:
                 ngrams_embedding = ngrams_embedding + ngram_e
        if noramlize: ngrams_embedding = ngrams_embedding/len(ngrams)
	
        
        W = dy.parameter(self.W)
        b = dy.parameter(self.b)

        if sum_embeddings: 
        
        	result = ngrams_embedding + w_embedding + b
        else:
        	result = W*dy.concatenate([ngrams_embedding, w_embedding])  + b

        return result

class ComplexEncoder(object):

    def __init__(self, inp_size, model, W2I, CHAR2I):

        self.embedding_encoder = EmbeddingEncoder(inp_size, model, W2I)
        self.LSTM_encoder = LSTMEncoder(len(CHAR2I), model, CHAR2I)

        self.W = model.add_parameters((EMBEDDING_SIZE, EMBEDDING_SIZE*2))

    def encode(self, w):

        lstm_encoding = self.LSTM_encoder.encode(w)
        embedding_encoding = self.embedding_encoder.encode(w)
        W = dy.parameter(self.W)

        return W * dy.concatenate([embedding_encoding, lstm_encoding])




from utils import *

words = read_words("words.txt")
ngrams = read_words("ngrams.txt")
W2I, I2W = generate_index_mapping(words)

NGRAM2I, I2NGRAM = generate_index_mapping(ngrams)
TRAIN = create_dataset("../datasets/deps_train.csv")
DEV = create_dataset("../datasets/deps_dev.csv")
TEST = create_dataset("../datasets/deps_test.csv")
NUMBER2I, I2NUMBER = generate_index_mapping(["sg", "pl", "-"], include_special_tokens = False)
VERB_SUFFIXES = get_verb_suffixes(words, verbs = True)
ARGUMENTS_SUFFIXES = get_verb_suffixes(words, verbs = False)
print "TRAIN SIZE: {}; DEV SIZE: {}".format(len(TRAIN), len(DEV))

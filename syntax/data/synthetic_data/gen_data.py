import os
import nltk
import random

# Define a probabilistic context-free grammar (PCFG)
pcfg_grammar_str1 = """
    S -> 'John' [0.1] | 'Mary' [0.1] | 'Bob' [0.1] | 'Sue' [0.1] | 'Tim' [0.1] | 'Tom' [0.1] | 'Alice' [0.1] | 'Jim' [0.1] | 'Anna' [0.1] | 'Sophie' [0.1]  
    V -> 'sees' [0.2] | 'likes' [0.2] | 'hates' [0.2] | 'kicks' [0.2] | 'finds' [0.2] 
    O -> 'apples' [0.1] | 'bananas' [0.1] | 'cars' [0.1] | 'balls' [0.1] | 'books' [0.1] | 'phones' [0.1] | 'shirts' [0.1] | 'hats' [0.1] | 'shoes' [0.1] | 'bags' [0.1] 
"""

pcfg_grammar_str2 = """
    S -> 'John' [0.1] | 'Mary' [0.1] | 'Bob' [0.1] | 'Sue' [0.1] | 'Tim' [0.1] | 'Tom' [0.1] | 'Alice' [0.1] | 'Jim' [0.1] | 'Anna' [0.1] | 'Sophie' [0.1]  
    V -> 'sees' [0.2] | 'loves' [0.2] | 'calls' [0.2] | 'knows' [0.2] | 'saw' [0.2] 
    O -> 'Emma' [0.1] | 'Lucas' [0.1] | 'Olivia' [0.1] | 'Noah' [0.1] | 'Liam' [0.1] | 'Ava' [0.1] | 'Ethan' [0.1] | 'Mia' [0.1] | 'Emily' [0.1] | 'Jacob' [0.1]
"""

swappable_sentences = [
    "Dogs love humans",
    "Tom knows Mary",
    "Kids love parents",
    "John likes Mary",
]



# Function to sample a production
def sample_production(grammar, symbol):
    # Get a list of productions from the grammar that have the right left-hand side
    productions = grammar.productions(lhs=symbol)
    # Choose a production at random, respecting the probabilities
    total = sum(prod.prob() for prod in productions)
    r = random.uniform(0, total)
    upto = 0.0
    for prod in productions:
        upto += prod.prob()
        if upto > r:
            return prod
    assert False, "Shouldn't get here"

# Function to sample a sentence
def sample_sentence(grammar, symbol=nltk.Nonterminal('H')):
    # Sample a production
    prod = sample_production(grammar, symbol)
    # Use the production to extend the sentence
    sentence = []
    for sym in prod.rhs():
        if isinstance(sym, nltk.grammar.Nonterminal):
            sentence += sample_sentence(grammar, sym)
        else:
            sentence.append(sym)
    return sentence

# Sample a sentence
for word_order in ["svo", "sov", "osv", "ovs", "vos", "vso"]:
    os.makedirs(f"{word_order}", exist_ok=True)
    with open(f"{word_order}/test.csv", "w") as f:
        e1, e2, e3 = word_order
        pcfg_grammar_str1 = f"H -> {e1.upper()} {e2.upper()} {e3.upper()} [1.0]\n"
        pcfg_grammar = nltk.PCFG.fromstring(pcfg_grammar_str1 + pcfg_grammar_str2)
        f.write('original_sent,main_verb,reordered_sent\n')

        for _ in range(100):
            tokens = sample_sentence(pcfg_grammar)
            tokens = [t.lower() for t in tokens]
            s_index = [e1, e2, e3].index("s")
            v_index = [e1, e2, e3].index("v")
            o_index = [e1, e2, e3].index("o")
            reordered_sent = " ".join(tokens) + "."
            original_sent = " ".join([tokens[s_index], tokens[v_index], tokens[o_index]]) + "."
            f.write(f"{original_sent},{tokens[v_index]},{reordered_sent}\n")

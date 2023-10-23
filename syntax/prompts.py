prompt_templates = {
    "main_verb_and_subj_std": {
        "instruction": "You are an expert in linguistics. Imagine a language that is the same as English with the only exception being that it uses the {order_description} order instead of the subject-verb-object order. Your task is to identify the main verb and the main subject in a sentence in this imaginary language.\n", 
        "english_instruction": "You are an expert in linguistics. Your task is to identify the main verb and the main subject in an English sentence.\n",
        "prediction": "Show the main verb (a single word) and its subject (also a single word) after the prefix 'Main verb and subject: '.\nSentence: {reordered_sent}\n",
    },
    "main_verb_and_subj_cot": {
        "instruction": "You are an expert in linguistics. Imagine a language that is the same as English with the only exception being that it uses the {order_description} order instead of the subject-verb-object order. Your task is to identify the main verb and the main subject in a sentence in this imaginary language.\n", 
        "english_instruction": "You are an expert in linguistics. Your task is to identify the main verb and the main subject in an English sentence.\n",
        "prediction": "Show the main verb (a single word) and its subject (also a single word) after the prefix 'Main verb and subject: '.\nSentence: {reordered_sent}\nLet's think step by step. ",
    },
    "reconstruct_std": {
        "instruction": "You are an expert in linguistics. Imagine a language that is the same as English only except that it uses the {order_description} order instead of the subject-verb-object order. Your task is to reconstruct the original sentence in English. You should only use the words in the same form as they appear in the given sentence.\n",
        "english_instruction": "",
        "prediction": "Sentence: {reordered_sent}\nShow the original sentence the prefix 'Original sentence: '.\n",
    },
    "reconstruct_cot": {
        "instruction": "You are an expert in linguistics. Imagine a language that is the same as English only except that it uses the {order_description} order instead of the subject-verb-object order. Your task is to reconstruct the original sentence in English. You should only use the words in the same form as they appear in the given sentence.\n",
        "english_instruction": "",
        "prediction": "Sentence: {reordered_sent}\nLet's think step by step. Show the original sentence at the end with the prefix 'Original sentence: '.\n",
    },
}
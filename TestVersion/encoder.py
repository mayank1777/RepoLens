import pandas as pd
import numpy as np


val_list = []

def load_vals(name):
    global val_list
    val_list = []
    with open(name + '.txt', 'r') as f:
        for val in f:
            val_list.append(val.strip())
    return np.load(name+'.npy')

def get_float(language_str):
    input_data = {}
    total_bytes = 0
    entries = language_str.split(';')
    for entry in entries:
        parts = entry.split(':')
        if len(parts) == 2:
            lang = parts[0].strip()
            bytes = int(parts[1].strip())
            input_data[lang] = bytes
            total_bytes += bytes
    if total_bytes == 0:  
        return np.zeros(len(val_list))
    percentage_vector = np.array([input_data.get(lang, 0) / total_bytes for lang in val_list])
    return percentage_vector

def get_bin(topic_str):
    topics = topic_str.split(';')
    for i in range(0, len(topics)):
        topics[i] = topics[i].strip()
    bin_vector = np.zeros(len(val_list))
    for i in range(0, len(val_list)):
        if val_list[i] in topics:
            bin_vector[i] = 1
    return bin_vector
    
def extract_lang(data):
    unique_vals = set()

    for val in data:
        languages = val.split(';')
        for language in languages:
            language_name = language.split(':')[0].strip()
            if language_name:
                unique_vals.add(language_name)
    
    language_list = sorted(unique_vals)
    with open('lang.txt', 'w') as f:
        for lang in language_list:
            f.write(f"{lang}\n")

    global val_list
    val_list = language_list
    vectors = []
    for val in data:
        vectors.append(get_float(val))
    
    lang_matrix = np.array(vectors)
    np.save('lang.npy', lang_matrix)

def extract_topic(data):
    unique_vals = set()

    for val in data:
        topics = val.split(';')
        for topic in topics:
            topic_name = topic.strip()
            if topic_name:
                unique_vals.add(topic_name)
    
    topic_list = sorted(unique_vals)
    with open('topic.txt', 'w') as f:
        for topic in topic_list:
            f.write(f"{topic}\n")
    
    global val_list
    val_list = topic_list

    vectors = []
    for val in data:
        vectors.append(get_bin(val))
    
    topic_matrix = np.array(vectors)
    np.save('topic.npy', topic_matrix)
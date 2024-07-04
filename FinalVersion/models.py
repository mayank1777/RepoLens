import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import pickle

from transformers import BertModel, BertTokenizer
import torch

CurrModel = None
CurrTokenizer = None

def train_tf(name, data, features):
    tfidf_vectorizer = TfidfVectorizer(analyzer='word', stop_words='english', max_features=features)

    tfidf_matrix = tfidf_vectorizer.fit_transform(data)
    #tfidf_vectorizer.get_feature_names_out():

    with open(name + '_tfmat', 'wb') as f:
        pickle.dump(tfidf_matrix, f)

    with open(name + '_tfvec', 'wb') as f:
        pickle.dump(tfidf_vectorizer, f)

def train_doc(name, data, features, win_size, min_cnt):
    train_corpus = [TaggedDocument(words=text.split(), tags=[str(i)]) for i, text in enumerate(data)]

    model = Doc2Vec(train_corpus, vector_size=features, window=win_size, min_count=min_cnt, workers=4, epochs=40)

    model.save(name + '_d2v')

def train_bert(name, data, batch):

    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    model.train()

    embedding_matrix = []

    for i in range(0, len(data), batch):
        texts = data[i:i+batch].tolist()

        encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors='pt', max_length=512)
        encoded_input = {key: val.to(model.device) for key, val in encoded_input.items()}

        with torch.no_grad():
            outputs = model(**encoded_input)

        embeddings = outputs.last_hidden_state[:, 0, :]
        embedding_matrix.append(embeddings.cpu().numpy())

        print(i)
    
    embedding_matrix = np.concatenate(embedding_matrix, axis=0)
    np.save(name + '_bert', embedding_matrix)

def load_tf(name):
    global CurrModel

    with open(name + '_tfvec', 'rb') as f:
        CurrModel = pickle.load(f)

    with open(name + '_tfmat', 'rb') as f:
        loaded_matrix = pickle.load(f)
    
    return loaded_matrix

def get_tf(content):
    return CurrModel.transform([content])

def load_d2v(name, length):
    global CurrModel
    CurrModel = Doc2Vec.load(name + '_d2v')
    return np.array([CurrModel.dv[str(i)] for i in range(length)])

def get_d2v(content):
    return CurrModel.infer_vector(content.split())

def load_bert(name):
    global CurrModel
    global CurrTokenizer
    CurrTokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    CurrModel = BertModel.from_pretrained('bert-base-uncased')
    CurrModel.eval()
    return np.load(name + '_bert.npy')

def get_bert(content):
    encoded_input = CurrTokenizer(content, return_tensors='pt', truncation=True, max_length=512, padding='max_length')
    with torch.no_grad():
        output = CurrModel(**encoded_input)
    embedding = output.last_hidden_state[:, 0, :].numpy()
    return embedding


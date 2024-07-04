import pandas as pd
import models
import encoder
import gitapi


data = pd.read_csv('popular.csv')
data.fillna('', inplace=True)
data['Description'] = data['Description'].apply(gitapi.preprocess_content)

encoder.extract_lang(data['Languages'])
encoder.extract_topic(data['Topics'])
models.train_tf('desc', data['Description'], 10000)
models.train_tf('read', data['README'], 10000)
models.train_doc('read', data['README'], 100, 5, 1)

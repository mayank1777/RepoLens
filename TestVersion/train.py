import pandas as pd
import models
import encoder
import gitapi

data = pd.read_csv('test_data.csv')
data.fillna('', inplace=True)
data['Description'] = data['Description'].apply(gitapi.preprocess_content)

encoder.extract_lang(data['Languages'])
encoder.extract_topic(data['Topics'])
models.train_tf('desc', data['Description'], 2000)
models.train_tf('readme', data['README'], 5000)
models.train_doc('readme', data['README'], 100, 5, 1)

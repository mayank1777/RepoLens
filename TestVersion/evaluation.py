import numpy as np
import pandas as pd
import models
import encoder
import gitapi
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

def jaccard_similarity(vector, matrix):
    intersection = np.sum(np.logical_and(matrix, vector), axis=1, dtype=float)
    union = np.sum(np.logical_or(matrix, vector), axis=1)

    zero = (union == 0)
    nonzero = (union != 0)
    intersection[nonzero] /= union[nonzero]
    intersection[zero] = 0

    return intersection

data = pd.read_csv('test_data.csv')
data.fillna('', inplace=True)

desc = pd.DataFrame(data['Description'])
desc = desc.applymap(gitapi.preprocess_content)

def score(w1, w2, w3, w4):
    result = 0

    sim1 = []
    sim2 = []
    sim3 = []
    sim4 = []

    model_matrix = models.load_tf('desc')

    for ind in range(0, len(data)):
        content = desc.iloc[ind]['Description']
        model_vector = models.get_tf(content)
        sim = cosine_similarity(model_vector, model_matrix)[0]
        sim1.append(sim)

    enc_matrix = encoder.load_vals('topic')

    for ind in range(0, len(data)):
        content = data.iloc[ind]['Topics']
        model_vector = encoder.get_bin(content)
        sim = jaccard_similarity(model_vector, enc_matrix)
        sim2.append(sim)

    model_matrix = models.load_tf('readme')

    for ind in range(0, len(data)):
        content = data.iloc[ind]['README']
        model_vector = models.get_tf(content)
        sim = cosine_similarity(model_vector, model_matrix)[0]
        sim3.append(sim)

    model_matrix = models.load_d2v('readme', len(data))

    for ind in range(0, len(data)):
        content = data.iloc[ind]['README']
        model_vector = [models.get_d2v(content)]
        sim = cosine_similarity(model_vector, model_matrix)[0]
        sim4.append(sim)

    for ind in range(0, len(data)):
        similarity = w1 * sim1[ind] + w2 * sim2[ind] + w3 * sim3[ind] + w4 * sim4[ind]
        top_indices = np.argsort(similarity)[::-1][:6] 

        precision = 0
        for ind2 in top_indices:
            if ind == ind2:
                continue
            if (ind//6) == (ind2//6):
                precision += 1
        
        precision /= 5
        #print(precision)
        result += precision

    result /= len(data)
    print(result)
    return result

x = np.arange(0, 40, 0.5)
y = [score(i, 11.5, 10.5, 1) for i in x]

plt.figure(figsize=(8, 6))   
plt.plot(x, y)

plt.xlabel('w1')
plt.ylabel('score')

plt.grid(True)  # Optional: Adds a grid for easier visualization
plt.show()
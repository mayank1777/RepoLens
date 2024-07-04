import numpy as np
import pandas as pd
import gitapi
import models
import encoder
import asyncio
import asyncapi

from scipy.sparse import vstack, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches


async def main():

    data = pd.read_csv('popular.csv')
    data['Distance'] = 1000.0
    data['Tag'] = "POPULAR"
    length = len(data)

    indices = {}
    for i in range(0, length):
        owner = data.iloc[i][0]
        name = data.iloc[i][1]
        indices[(owner, name)] = i
    
    #print(indices)

    print('Welcome to RepoLens, please enter your github username')
    user = str(input())

    print("Loading your repositories...")

    details = []
    langs = []
    readmes = []

    repos = gitapi.get_user_repositories(user)
    starred = gitapi.get_starred_repositories(user)

    if not repos:
        repos = []

    if not starred:
        starred = []

    print("Created Repositories: " + str(len(repos)))
    print("Starred Repositories: " + str(len(starred)))

    for repo in starred:
        if not repo in repos:
            repos.append(repo)

    if len(repos) == 0:
        model_enc = encoder.load_vals('topic')
        print('It seems like this is your first time! Enter three topics you may like')
        tvec = np.zeros(len(encoder.val_list), dtype='float')
        
        choices = []

        for i in range(0, 3):
            choices.append(input().strip())
            choices[i] = get_close_matches(choices[i], encoder.val_list, n=1, cutoff=0.0)[0]

        print("Closest Matches:")
        print(choices)

        for choice in choices:
            tvec[encoder.val_list.index(choice)] = 1

    else:
        res = await asyncapi.fetch_all_repos_data(repos)

        for i in range(0, len(res), 3):
            detail = res[i+1]
            if not detail:
                continue
            lang = res[i+2]
            readme = res[i] 
            details.append(detail)
            langs.append(lang)
            if readme:
                readmes.append(readme)

    #print(langs)

    print("Include Trending Repositories y/n?")
    inp = input().lower()
    
    if inp == 'y':
        print("Getting Trending Repositories")
        trending = gitapi.fetch_top_repos_last_month()
        
        res = await asyncapi.fetch_all_repos_data(trending)
        ind = 0
        for i in range(0, len(res), 3):
            owner = trending[ind][0]
            name = trending[ind][1]
            if (owner, name) in indices:
                data.iloc[indices[((owner, name))]]['Distance'] = 1.0 + ind//50
                data.iloc[indices[((owner, name))]]['Tag'] = 'TRENDING'
            else:
                detail = res[i+1]
                if not detail:
                    continue
                indices[(owner, name)] = len(data)
                lang = res[i+2]
                readme = res[i]
                row = [owner, name, detail.get('description', ''), lang, ';'.join(detail.get('topics', [])), readme, 1.0 + ind//50, 'TRENDING']
                data.loc[len(data)] = row
            ind += 1

    print("Include Connected Repositories y/n?")
    inp = input().lower()

    if inp == 'y' and len(repos) > 0:
        print("Getting Connected Repositories")
        connections = await asyncapi.get_connected_repositories(user, 100)
        connect = []
        for c in connections:
            connect.append((c[0], c[1]))

        res = await asyncapi.fetch_all_repos_data(connect)
        ind = 0
        for i in range(0, len(res), 3):
            owner = connect[ind][0]
            name = connect[ind][1]
            dist = connections[ind][2]
            if (owner, name) in indices:
                val = data.iloc[indices[((owner, name))]]['Distance']
                if dist < val:
                    data.iloc[indices[((owner, name))]]['Distance'] = dist
                    data.iloc[indices[((owner, name))]]['Tag'] = 'CONNECTED'
            else:
                detail = res[i+1]
                if not detail:
                    continue
                indices[(owner, name)] = len(data)
                lang = res[i+2]
                readme = res[i]
                row = [owner, name, detail.get('description', ''), lang, ';'.join(detail.get('topics', [])), readme, dist, 'CONNECTED']
                data.loc[len(data)] = row
            ind += 1

    data.fillna('', inplace=True)
    description = pd.DataFrame(data['Description'])
    data['Description'] = data['Description'].apply(gitapi.preprocess_content)

    

    #--------------------------------------------------
    model_matrix = models.load_tf('desc')
    vectors = []

    for detail in details:
        desc = detail.get('description', '')
        if desc:
            vectors.append(models.get_tf(gitapi.preprocess_content(desc)))

    for i in range(length, len(data)):
        desc = data.iloc[i]['Description']
        model_matrix = vstack([model_matrix, models.get_tf(desc)])

    #vectors = [models.get_tf('a file and photo management application and system')]

    if len(vectors) == 0:
        sim1 = np.zeros(len(data), dtype='float')
    else:
        vectors = vstack(vectors)
        model_vector = csr_matrix(vectors.mean(axis=0))
        sim1 = cosine_similarity(model_vector, model_matrix)[0]

    #--------------------------------------------------
    model_enc = encoder.load_vals('topic')
    vectors = []
    if len(repos) == 0:
        vectors.append(tvec)

    for detail in details:
        topics = ';'.join(detail.get('topics', []))
        if topics:
            vectors.append(encoder.get_bin(topics))

    for i in range(length, len(data)):
        topic = data.iloc[i]['Topics']
        model_enc = vstack([model_enc, encoder.get_bin(topic)])

    #vectors = []

    if len(vectors) == 0:
        sim2 = np.zeros(len(data), dtype = 'float')
    else:
        vectors = np.array(vectors)
        model_vector = vectors.mean(axis=0)
        sim2 = cosine_similarity([model_vector], model_enc)[0]

    #--------------------------------------------------        
    model_matrix = models.load_tf('read')
    vectors = []

    for readme in readmes:
        vectors.append(models.get_tf(readme))

    for i in range(length, len(data)):
        readme = data.iloc[i]['README']
        model_matrix = vstack([model_matrix, models.get_tf(readme)])

    #vectors = []

    if len(vectors) == 0:
        sim3 = np.zeros(len(data), dtype='float')
    else:
        vectors = vstack(vectors)
        model_vector = csr_matrix(vectors.mean(axis=0))
        sim3 = cosine_similarity(model_vector, model_matrix)[0]



    #--------------------------------------------------
    model_matrix = models.load_d2v('read', length)
    vectors = []

    for readme in readmes:
        vectors.append(models.get_d2v(readme))

    for i in range(length, len(data)):
        readme = data.iloc[i]['README']
        model_matrix = vstack([model_matrix, models.get_d2v(readme)])

    #vectors = []

    if len(vectors) == 0:
        sim4 = np.zeros(len(data), dtype='float')
    else:
        vectors = np.array(vectors)
        model_vector = vectors.mean(axis=0)
        sim4 = cosine_similarity([model_vector], model_matrix)[0]

    #--------------------------------------------------
    model_enc = encoder.load_vals('lang')
    vectors = []

    for lang in langs:
        vectors.append(encoder.get_float(lang))

    for i in range(length, len(data)):
        lang = data.iloc[i]['Languages']
        model_enc = vstack([model_enc, encoder.get_float(lang)])

    #vectors = []

    if len(vectors) == 0:
        sim5 = np.zeros(len(data), dtype = 'float')
    else:
        vectors = np.array(vectors)
        model_vector = vectors.mean(axis=0)
        sim5 = cosine_similarity([model_vector], model_enc)[0]

    #--------------------------------------------------  

    print("Filter Programming Languages? y/n")
    inp = input().lower()

    w5 = 0.0
    if inp == 'y':
        w5 = 1.2
    

    similarity = 1 * sim1 + 1.2 * sim2 + 0.8 * sim3 + 0.3 * sim4 + w5 * sim5
    for i in range(0, len(data)):
        dist = data.iloc[i]['Distance']
        similarity[i] *= (1 + (0.5/dist))
    top_indices = np.argsort(similarity)[::-1]

    data['Sim'] = similarity
    data.to_csv('debug.csv', index=False)

    print("\nTop Recommendations:\n")
    cnt = 0
    for index in top_indices:
        owner = data.iloc[index]['Owner']
        name = data.iloc[index]['Repository Name']
        if (owner, name) in repos:
            continue

        #print(index)
        print(data.iloc[index]['Tag'])
        print(owner+'/'+name)
        print(description.iloc[index]['Description'])
        print(data.iloc[index]['Topics'])
        if inp == 'y':
            print(data.iloc[index]['Languages'])
        #print(data2.iloc[index]['README'])
        print(f"Recommendation Score: {similarity[index]}")
        print(data.iloc[index]['Distance'])
        print("\n---\n")
        
        cnt += 1
        if cnt == 10:
            break

asyncio.run(main())
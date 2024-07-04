import asyncapi
import gitapi
import csv
import asyncio

headers = ['Owner', 'Repository Name', 'Description', 'Languages', 'Topics', 'README']

async def createcsv(name, data):
    with open(name + '.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        res = await asyncapi.fetch_all_repos_data(data)
        ind = 0
        for i in range(0, len(res), 3):
            owner = data[ind][0]
            name = data[ind][1]
            details = res[i+1]
            if not details:
                continue
            lang = res[i+2]
            readme = res[i]
            row = [owner, name, details.get('description', ''), lang, ';'.join(details.get('topics', [])), readme]
            writer.writerow(row)
            ind += 1

#Code to generate test data

repos = []
with open('category.csv', mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  
    for row in reader:
        repo = row[1].split('/')
        repos.append((repo[0], repo[1]))

asyncio.run(createcsv('test_data', repos))

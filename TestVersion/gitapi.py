import requests
import base64
import re
from datetime import datetime, timedelta

token = "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"

#PREPROCESS TEXT

def preprocess_content(content):
    # Replace newlines, carriage returns, and tabs with a single space
    content = re.sub(r'[\n\r\t]', ' ', content)
    # Convert to lowercase
    content = content.lower()
    # Remove HTML tags
    content = re.sub(r'<.*?>', '', content)
    # Remove URLs
    content = re.sub(r'http[s]?://\S+', '', content)
    # Only keep letters, digits
    content = re.sub(r'[^a-z0-9\s]', '', content)
    # Remove numbers
    content = re.sub(r'\b\d+\b', '', content)
    # Remove hexadecimals
    content = re.sub(r'\b0x[a-fA-F0-9]+\b', '', content)
    # Trim leading and trailing spaces
    content = content.strip()
    # Reduce multiple spaces to a single space
    content = re.sub(r'\s+', ' ', content)
    return content

#READ ME OF AN REPO

def fetch_readme_content(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return preprocess_content(content)
    else:
        print(f"Failed to fetch README content for {owner}/{repo}. Status code: {response.status_code}")
        return ""
    
#DETAILS OF A REPO

def fetch_repository_data(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch repository details for {owner}/{repo}. Status code: {response.status_code}")
        return None

#LANGUAGES IN A REPO

def fetch_languages(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        languages = response.json()
        return ('; '.join([f"{lang}: {lines}" for lang, lines in languages.items()]) if languages else "None")
    else:
        print(f"Failed to fetch languages for {owner}/{repo}. Status code: {response.status_code}")
        return None

#GET REPOS BY USER   

def get_user_repositories(username):
    url = f"https://api.github.com/users/{username}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        return [(repo['owner']['login'], repo['name']) for repo in repos]
    else:
        print(f"Failed to fetch repositories. Status code: {response.status_code}")
        return None

#GET REPOS STARRED BY USER 

def get_starred_repositories(username):
    url = f"https://api.github.com/users/{username}/starred"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        return [(repo['owner']['login'], repo['name']) for repo in repos]
    else:
        print(f"Failed to fetch starred repositories. Status code: {response.status_code}")
        return None

#GET MOST RECENT REPOS OF A USER

def fetch_recent_repos(username, limit=3):
    url = f"https://api.github.com/users/{username}/repos?sort=created&per_page={limit}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

#GET LIST OF FOLLOWING OF A USER

def fetch_following(username):
    url = f"https://api.github.com/users/{username}/following"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    return [user['login'] for user in response.json()] if response.status_code == 200 else []

#FIND CONNECTED REPOS

def get_connected_repositories(source_user, max_repos=50):
    from collections import deque

    # Initialize the queue with the source user and distance 0
    queue = deque([(source_user, 0)])
    seen_users = set([source_user])
    repo_set = set()
    ma = 0

    while queue and len(repo_set) < max_repos:
        current_user, current_distance = queue.popleft()
        if current_distance > 0:
            if current_distance > ma:
                print("Traversing Level " + str(current_distance))
                ma = current_distance
            repos = fetch_recent_repos(current_user)
            
            for repo in repos:
                repo_key = (repo['name'], repo['owner']['login'], current_distance)
                if len(repo_set) >= max_repos:
                    break
                repo_set.add(repo_key)
        
        if len(repo_set) < max_repos:
            following = fetch_following(current_user)
            for user in following:
                if user not in seen_users:
                    seen_users.add(user)
                    # Enqueue the user with the incremented distance
                    queue.append((user, current_distance + 1))

    return list(repo_set)

#TOP REPOS OF A PARTICULAR YEAR

def fetch_top_repos_by_year(year, max_repos=100):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = "https://api.github.com/search/repositories"
    query = f"created:{year}-01-01..{year}-12-31 sort:stars"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 100  # Maximum allowed by GitHub
    }
    
    repos = []
    page = 1

    while len(repos) < max_repos:
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            response_data = response.json()
            # Process each repo to extract owner and repo name
            for item in response_data['items']:
                owner = item['owner']['login']
                repo_name = item['name']
                repos.append((owner, repo_name))
                if len(repos) >= max_repos:
                    break
        else:
            print(f"Failed to fetch repositories for year {year}. Status code: {response.status_code}")
            break

        page += 1
        if len(response_data['items']) < 100:
            break  # Break if last page

    return repos[:max_repos]

#LIST OF POPULAR REPOS THROUGHOUT MANY YEARS

def fetch_popular(start_year=2008, end_year=2023):
    all_repos = {}
    for year in range(start_year, end_year + 1):
        print(f"Fetching top repositories for {year}")
        top_repos = fetch_top_repos_by_year(year)
        all_repos[year] = top_repos
    return all_repos

#TRENDING REPOS

def fetch_top_repos_last_month(max_repos=100):
    # Calculate dates for the last month
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = "https://api.github.com/search/repositories"
    query = f"created:{start_date_str}..{end_date_str} sort:stars"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos  # fetch up to max_repos in a single API call
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_data = response.json()
        repos = [(item['owner']['login'], item['name']) for item in response_data['items']]
        return repos
    else:
        print(f"Failed to fetch repositories. Status code: {response.status_code}, Message: {response.json().get('message')}")
        return []
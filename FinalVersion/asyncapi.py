import aiohttp
import asyncio
import base64
import re

token = "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"

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

async def fetch_readme_content(session, owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            return preprocess_content(content)
        else:
            #print(f"Failed to fetch README content for {owner}/{repo}. Status code: {response.status}")
            return ""

async def fetch_repository_data(session, owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            #print(f"Failed to fetch repository details for {owner}/{repo}. Status code: {response.status}")
            return None

async def fetch_languages(session, owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            languages = await response.json()
            return '; '.join([f"{lang}: {lines}" for lang, lines in languages.items()]) if languages else "None"
        else:
            #print(f"Failed to fetch languages for {owner}/{repo}. Status code: {response.status}")
            return None

async def fetch_all_repos_data(repos):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for owner, repo in repos:
            task_readme = fetch_readme_content(session, owner, repo)
            task_repo_data = fetch_repository_data(session, owner, repo)
            task_languages = fetch_languages(session, owner, repo)
            tasks.extend([task_readme, task_repo_data, task_languages])
        results = await asyncio.gather(*tasks)
        return results

from collections import deque

async def fetch_recent_repos(session, username, limit=2):
    url = f"https://api.github.com/users/{username}/repos?sort=created&per_page={limit}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        return []

async def fetch_following(session, username):
    url = f"https://api.github.com/users/{username}/following"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return [user['login'] for user in await response.json()]
        return []

async def get_connected_repositories(source_user, max_repos=50):
    queue = deque([(source_user, 0)])
    seen_users = set([source_user])
    repo_set = set()
    ma = 0

    async with aiohttp.ClientSession() as session:
        while queue and len(repo_set) < max_repos:
            current_user, current_distance = queue.popleft()
            if current_distance > 0:
                if current_distance > ma:
                    print("Traversing Level " + str(current_distance))
                    ma = current_distance
                repos = await fetch_recent_repos(session, current_user)
                
                for repo in repos:
                    repo_key = (repo['owner']['login'], repo['name'], current_distance)
                    if len(repo_set) >= max_repos:
                        break
                    repo_set.add(repo_key)
            
            if len(repo_set) < max_repos:
                following = await fetch_following(session, current_user)
                for user in following:
                    if user not in seen_users:
                        seen_users.add(user)
                        queue.append((user, current_distance + 1))

    return list(repo_set)
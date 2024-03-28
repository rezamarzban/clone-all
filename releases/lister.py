import requests

# GitHub username
username = "rezamarzban"

# GitHub API base URL
base_url = f"https://api.github.com/users/{username}/repos"

# Function to list all repositories of a GitHub user
def list_repositories():
    try:
        # Initialize an empty list to store repositories
        all_repos = []

        # Start with the first page
        page = 1

        # Fetch repositories until there are no more pages
        while True:
            # Get repositories data for the current page
            params = {'page': page, 'per_page': 100}  # 100 repositories per page (maximum)
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

            repos_data = response.json()
            # Add repositories from the current page to the list
            all_repos.extend(repos_data)

            # Move to the next page
            if 'next' in response.links:
                page += 1
            else:
                break

        # Print repository names
        #print(f"Repositories of user {username}:")
        for repo in all_repos:
            print(repo["name"])
    except Exception as e:
        print(f"Error listing repositories: {e}")

list_repositories()

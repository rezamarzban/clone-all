import requests
import os

# GitHub username
username = "rezamarzban"

# Function to download releases from a repository
def download_releases(repo_name):
    # GitHub API URL for releases
    releases_url = f"https://api.github.com/repos/{username}/{repo_name}/releases"

    # Get releases data
    response = requests.get(releases_url)
    releases_data = response.json()

    # Create a directory for the repository if it doesn't exist
    if not os.path.exists(repo_name):
        os.makedirs(repo_name)

    # Download assets for each release
    for release in releases_data:
        tag_name = release.get("tag_name")
        release_folder = os.path.join(repo_name, tag_name)
        if not os.path.exists(release_folder):
            os.makedirs(release_folder)
        assets = release.get("assets", [])
        for asset in assets:
            asset_url = asset.get("browser_download_url")
            asset_name = asset.get("name")
            if asset_url:
                print(f"Downloading {asset_name} from {repo_name}...")
                # Download the asset
                response = requests.get(asset_url)
                # Save the asset to a file
                asset_path = os.path.join(release_folder, asset_name)
                with open(asset_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {asset_name} from {repo_name}")


# Read repository names from list.txt
with open("list.txt", "r") as file:
    repositories = file.readlines()
    repositories = [repo.strip() for repo in repositories]

# Download releases for each repository
for repo_name in repositories:
    download_releases(repo_name)

import os
import requests
import yaml
import argparse

from github import Github
# Authentication is defined via github.Auth
from github import Auth

# Function to load repositories and required files from a YAML file
def load_config(yaml_file):
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)
    return config['repositories'], config['core_files']

# Function to check if certain files exist in the repo
def check_repo_setup(repo_name, core_files, custom_files, token, owner):
    url = f'https://api.github.com/repos/{owner}/{repo_name}/contents/'
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        contents = response.json()
        found_files = [file['name'] for file in contents]

        # Check for missing core and custom files
        missing_files = [file for file in core_files + custom_files if file not in found_files]
        return missing_files
    return None

# Function to update issues in each repository
def update_issues(repo_name, missing_files, token, owner):
    # using an access token
    auth = Auth.Token(token)
    g = Github(auth=auth)
    
    repo = g.get_repo(f'{owner}/{repo_name}')
    issues = repo.get_issues(state='open')

    for issue in issues:
        if not missing_files:
            issue.create_comment(f"All required files are set up in {repo_name}.")
        else:
            issue.create_comment(f"The following files are missing in {repo_name}: {', '.join(missing_files)}")
                
    # To close connections after use
    g.close()

# Main function to check all repos and update issues
def check_all_repos(yaml_file, token, owner):
    repositories, core_files = load_config(yaml_file)
    for repo in repositories:
        repo_name = repo['name']
        custom_files = repo.get('custom_files', [])
        missing_files = check_repo_setup(repo_name, core_files, custom_files, token, owner)
        update_issues(repo_name, missing_files, token, owner)

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Check repo setup and update GitHub issues.")
    parser.add_argument('--yaml-file', type=str, default='repos.yml', help="Path to the YAML file with repository config.")
    parser.add_argument('--token', type=str, default=os.getenv('TOKEN'), help="GitHub API token (default from environment variable).")
    parser.add_argument('--owner', type=str, default=os.getenv('REPO_OWNER'), help="Repository owner (default from environment variable).")
    
    args = parser.parse_args()

    # Run the check with overrides for token and owner if provided
    check_all_repos(args.yaml_file, args.token, args.owner)

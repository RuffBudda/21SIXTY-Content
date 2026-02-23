#!/usr/bin/env python3
"""
Script to automatically update the version number in frontend/index.html
based on the current GitHub commit count + 1.
"""

import re
import subprocess
import sys
from pathlib import Path

def fetch_from_github():
    """Fetch the latest changes from GitHub"""
    try:
        print("Fetching latest changes from GitHub...")
        result = subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            capture_output=True,
            text=True,
            check=True
        )
        print("Successfully fetched from GitHub")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to fetch from GitHub: {e.stderr}", file=sys.stderr)
        return False

def get_commit_count():
    """Get the current commit count from GitHub"""
    # Always fetch first to ensure we have the latest commit count
    fetch_from_github()
    
    try:
        # Get commit count from origin/main (should be up-to-date after fetch)
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'origin/main'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_count = int(result.stdout.strip())
        return commit_count
    except subprocess.CalledProcessError as e:
        print(f"Error getting commit count from origin/main: {e}", file=sys.stderr)
        # Fallback: try local commit count
        try:
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            commit_count = int(result.stdout.strip())
            print(f"Warning: Using local commit count ({commit_count})", file=sys.stderr)
            return commit_count
        except subprocess.CalledProcessError:
            print("Error: Could not get commit count from git", file=sys.stderr)
            sys.exit(1)

def update_version_in_file(file_path, new_version):
    """Update version number in the HTML file"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"Error: File {file_path} not found", file=sys.stderr)
        sys.exit(1)
    
    # Read the file
    content = file_path.read_text(encoding='utf-8')
    
    # Pattern to match version numbers in title tag and h1 tag
    # Supports both old format (<h1>21SIXTY CONTENT GEN v26</h1>) and new format (<h1>21SIXTY CONTENT GEN <span class="version">v26</span></h1>)
    updated_content = content
    changes_made = False
    
    # Update title tag
    title_pattern = r'<title>21SIXTY CONTENT GEN v\d+</title>'
    title_replacement = f'<title>21SIXTY CONTENT GEN v{new_version}</title>'
    if re.search(title_pattern, updated_content):
        updated_content = re.sub(title_pattern, title_replacement, updated_content)
        changes_made = True
    
    # Update h1 tag - check for new format first (with span), then old format (without span), then no version
    # Pattern 1: With span (new format): <h1 class="title">21SIXTY CONTENT GEN <span class="version">v26</span></h1>
    h1_with_span_pattern = r'(<h1 class="title">21SIXTY CONTENT GEN\s*)<span class="version">v\d+</span>(</h1>)'
    if re.search(h1_with_span_pattern, updated_content):
        updated_content = re.sub(h1_with_span_pattern, f'\\1<span class="version">v{new_version}</span>\\2', updated_content)
        changes_made = True
    # Pattern 2: Old format with inline version: <h1 class="title">21SIXTY CONTENT GEN v26</h1>
    elif re.search(r'<h1 class="title">21SIXTY CONTENT GEN v\d+</h1>', updated_content):
        updated_content = re.sub(
            r'<h1 class="title">21SIXTY CONTENT GEN v\d+</h1>',
            f'<h1 class="title">21SIXTY CONTENT GEN <span class="version">v{new_version}</span></h1>',
            updated_content
        )
        changes_made = True
    # Pattern 3: No version at all: <h1 class="title">21SIXTY CONTENT GEN</h1>
    elif re.search(r'<h1 class="title">21SIXTY CONTENT GEN</h1>', updated_content):
        updated_content = re.sub(
            r'<h1 class="title">21SIXTY CONTENT GEN</h1>',
            f'<h1 class="title">21SIXTY CONTENT GEN <span class="version">v{new_version}</span></h1>',
            updated_content
        )
        changes_made = True
    
    # Check if anything changed
    if not changes_made:
        print(f"No version numbers found to update in {file_path}")
        return False
    
    # Write back to file
    file_path.write_text(updated_content, encoding='utf-8')
    print(f"Updated version to v{new_version} in {file_path}")
    return True

def commit_and_push(file_path, version):
    """Commit and push the version update to GitHub"""
    try:
        # Ensure we're up-to-date before pushing
        fetch_from_github()
        
        # Check if there are any uncommitted changes that aren't the version update
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        uncommitted = [line for line in status_result.stdout.strip().split('\n') if line.strip()]
        version_file_change = [line for line in uncommitted if 'frontend/index.html' in line]
        
        if version_file_change:
            # Stage the version update
            print(f"Staging version update...")
            subprocess.run(
                ['git', 'add', str(file_path)],
                check=True,
                capture_output=True
            )
            
            # Commit
            print(f"Committing version update...")
            commit_message = f"Update version to v{version}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                check=True,
                capture_output=True
            )
            
            # Fetch again before push to ensure we're up-to-date
            fetch_from_github()
            
            # Push to GitHub
            print(f"Pushing to GitHub...")
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                check=True
            )
            print(f"Successfully pushed version v{version} to GitHub")
            return True
        else:
            print("No version file changes to commit")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}", file=sys.stderr)
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error details: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}", file=sys.stderr)
        return False

def main():
    """Main function"""
    # Get commit count and add 1
    commit_count = get_commit_count()
    new_version = commit_count + 1
    
    print(f"Current commit count: {commit_count}")
    print(f"New version number: v{new_version}")
    
    # Update the HTML file
    html_file = Path(__file__).parent / 'frontend' / 'index.html'
    updated = update_version_in_file(html_file, new_version)
    
    if updated:
        print(f"\nVersion updated successfully to v{new_version}")
        
        # Automatically commit and push
        if commit_and_push(html_file, new_version):
            print(f"\nVersion v{new_version} has been committed and pushed to GitHub")
        else:
            print(f"\n⚠ Version file updated, but git push failed. Please commit and push manually:")
            print(f"  git add frontend/index.html")
            print(f"  git commit -m 'Update version to v{new_version}'")
            print(f"  git push origin main")
    else:
        print("\nWarning: No changes made")
        sys.exit(1)

if __name__ == '__main__':
    main()


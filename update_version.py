#!/usr/bin/env python3
"""
Script to automatically update the version number in frontend/index.html
based on the current GitHub commit count + 1.
"""

import re
import subprocess
import sys
from pathlib import Path

def get_commit_count():
    """Get the current commit count from GitHub"""
    try:
        # First, fetch the latest from GitHub
        subprocess.run(['git', 'fetch', 'origin', 'main'], 
                      check=False, capture_output=True)
        
        # Get commit count from origin/main
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'origin/main'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_count = int(result.stdout.strip())
        return commit_count
    except subprocess.CalledProcessError as e:
        print(f"Error getting commit count: {e}", file=sys.stderr)
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
    # Matches: v23, v26, etc. - more specific patterns
    patterns = [
        (r'<title>21SIXTY CONTENT GEN v\d+</title>', f'<title>21SIXTY CONTENT GEN v{new_version}</title>'),
        (r'<h1 class="title">21SIXTY CONTENT GEN v\d+</h1>', f'<h1 class="title">21SIXTY CONTENT GEN v{new_version}</h1>'),
    ]
    
    updated_content = content
    changes_made = False
    
    for pattern, replacement in patterns:
        if re.search(pattern, updated_content):
            updated_content = re.sub(pattern, replacement, updated_content)
            changes_made = True
    
    # Check if anything changed
    if not changes_made:
        print(f"No version numbers found to update in {file_path}")
        return False
    
    # Write back to file
    file_path.write_text(updated_content, encoding='utf-8')
    print(f"Updated version to v{new_version} in {file_path}")
    return True

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
        print("Don't forget to commit and push the changes!")
    else:
        print("\nWarning: No changes made")
        sys.exit(1)

if __name__ == '__main__':
    main()


"""GitHub repository analysis tools."""

from fastmcp import FastMCP
import os
import subprocess
from typing import List
import tempfile
import shutil
from pathlib import Path
import hashlib
import git

mcp = FastMCP(
    "GitHub Tools",
    dependencies=[
        "gitpython",
    ]
)

def clone_repo(repo_url: str) -> str:
    """Clone a repository and return the path. If repository is already cloned in temp directory, reuse it."""
    
    if not repo_url.startswith("https://github.com/") and os.path.exists(repo_url):
        return repo_url

    # Create a deterministic directory name based on repo URL
    repo_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:12]
    temp_dir = os.path.join(tempfile.gettempdir(), f"github_tools_{repo_hash}")
    
    # If directory exists and is a valid git repo, return it
    if os.path.exists(temp_dir):
        try:
            repo = git.Repo(temp_dir)
            if not repo.bare and repo.remote().url == repo_url:
                return temp_dir
        except:
            # If there's any error with existing repo, clean it up
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Create directory and clone repository
    os.makedirs(temp_dir, exist_ok=True)
    try:
        git.Repo.clone_from(repo_url, temp_dir)
        return temp_dir
    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Failed to clone repository: {str(e)}")

def get_directory_tree(path: str, prefix: str = "") -> str:
    """Generate a tree-like directory structure string"""
    output = ""
    entries = os.listdir(path)
    entries.sort()
    
    for i, entry in enumerate(entries):
        if entry.startswith('.git'):
            continue
            
        is_last = i == len(entries) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = "    " if is_last else "│   "
        
        entry_path = os.path.join(path, entry)
        output += prefix + current_prefix + entry + "\n"
        
        if os.path.isdir(entry_path):
            output += get_directory_tree(entry_path, prefix + next_prefix)
            
    return output

@mcp.tool()
def git_directory_structure(repo_url: str) -> str:
    """
    Clone or use existing local directory as a git repository and return its directory structure in a tree format.
    
    Args:
        repo_url: The URL of the Git repository or local directory
        
    Returns:
        A string representation of the repository's directory structure
    """
    try:
        # Clone the repository
        repo_path = clone_repo(repo_url)
        
        # Generate the directory tree
        tree = get_directory_tree(repo_path)
        return tree
            
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def git_read_important_files(repo_url: str, file_paths: List[str]) -> dict[str, str]:
    """
    Read the contents of specified files in a given git repository or local directory.
    
    Args:
        repo_url: The URL of the Git repository or local directory
        file_paths: List of file paths to read (relative to repository root)
        
    Returns:
        A dictionary mapping file paths to their contents
    """
    try:
        # Clone the repository
        repo_path = clone_repo(repo_url)
        results = {}
        
        for file_path in file_paths:
            full_path = os.path.join(repo_path, file_path)
            
            # Check if file exists
            if not os.path.isfile(full_path):
                results[file_path] = f"Error: File not found"
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    results[file_path] = f.read()
            except Exception as e:
                results[file_path] = f"Error reading file: {str(e)}"
        
        return results
            
    except Exception as e:
        return {"error": f"Failed to process repository: {str(e)}"}

def modify_file_content(file_path: str, content: str, start_line: int = None, end_line: int = None) -> None:
    """
    Modify content of a file, either completely or partially based on line numbers.
    
    Args:
        file_path: Path to the file to modify
        content: New content to write
        start_line: Starting line number (1-based) for partial modification
        end_line: Ending line number (1-based) for partial modification
    """
    if start_line is None or end_line is None:
        # Full file replacement
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return

    # Read existing content
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Adjust line numbers to 0-based index
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)

    # Replace specified lines with new content
    new_lines = content.splitlines()
    lines[start_idx:end_idx] = [line + '\n' for line in new_lines]

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


@mcp.tool()
def git_write_file(repo_url: str, file_path: str, content: str) -> dict[str, str]:
    """
    Write content to a file in a given git repository or local directory.
    
    Args:
        repo_url: The URL of the Git repository or local directory
        file_path: Path to the file to write (relative to repository root)
        content: Content to write to the file
        
    Returns:
        A dictionary containing the status of the operation
    """
    try:
        # Clone the repository
        repo_path = clone_repo(repo_url)
        full_path = os.path.join(repo_path, file_path)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write the content to the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {
            "status": "success",
            "message": f"Successfully wrote content to {file_path}",
            "file_path": file_path
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to write file: {str(e)}",
            "file_path": file_path
        } 

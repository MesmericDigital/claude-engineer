import os
import shutil
import glob
import json
import logging
from dotenv import load_dotenv
from PIL import Image

# Load environment variables from .env file
load_dotenv()

def create_folders(paths):
    results = []
    for path in paths:
        try:
            # Use os.makedirs with exist_ok=True to create nested directories
            os.makedirs(path, exist_ok=True)
            results.append(f"Folder(s) created: {path}")
        except Exception as e:
            results.append(f"Error creating folder(s) {path}: {str(e)}")
    return "\n".join(results)

def create_files(files):
    global file_contents
    results = []
    
    # Handle different input types
    if isinstance(files, str):
        # If a string is passed, assume it's a single file path
        files = [{"path": files, "content": ""}]
    elif isinstance(files, dict):
        # If a single dictionary is passed, wrap it in a list
        files = [files]
    elif not isinstance(files, list):
        return "Error: Invalid input type for create_files. Expected string, dict, or list."
    
    for file in files:
        try:
            if not isinstance(file, dict):
                results.append(f"Error: Invalid file specification: {file}")
                continue
            
            path = file.get('path')
            content = file.get('content', '')
            
            if path is None:
                results.append(f"Error: Missing 'path' for file")
                continue
            
            dir_name = os.path.dirname(path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(content)
            
            file_contents[path] = content
            results.append(f"File created and added to system prompt: {path}")
        except Exception as e:
            results.append(f"Error creating file: {str(e)}")
    
    return "\n".join(results)

def read_multiple_files(paths, recursive=False):
    global file_contents
    results = []

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        try:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                if recursive:
                    file_paths = glob.glob(os.path.join(abs_path, '**', '*'), recursive=True)
                else:
                    file_paths = glob.glob(os.path.join(abs_path, '*'))
                file_paths = [f for f in file_paths if os.path.isfile(f)]
            else:
                file_paths = glob.glob(abs_path, recursive=recursive)

            for file_path in file_paths:
                abs_file_path = os.path.abspath(file_path)
                if os.path.isfile(abs_file_path):
                    if abs_file_path not in file_contents:
                        with open(abs_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        file_contents[abs_file_path] = content
                        results.append(f"File '{abs_file_path}' has been read and stored in the system prompt.")
                    else:
                        results.append(f"File '{abs_file_path}' is already in the system prompt. No need to read again.")
                else:
                    results.append(f"Skipped '{abs_file_path}': Not a file.")
        except Exception as e:
            results.append(f"Error reading path '{path}': {str(e)}")

    return "\n".join(results)

def list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

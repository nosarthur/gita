import os
from pygtrie import CharTrie
from . import utils

def get_workspaces() -> CharTrie:
    """Gets all the workspaces as a trie structure.

    The keys is the path to the workspace, and the values is the group assigned to them

    Returns:
        CharTrie: [A trie with the workspace paths as keys and groups as values]
    """
    workspace_file = utils.get_config_fname('workspace_path')
    workspaces = CharTrie()
    if os.path.isfile(workspace_file) and os.stat(workspace_file).st_size > 0:
        with open(workspace_file) as f:
            for line in f:
                if line:
                    current = line.rstrip().split(',')
                    workspaces[current[0]] = current[1]
    return workspaces

def get_workspace_group(path: str) -> str:
    """Gets the group assigned to the current path.
    
    A group is assigned if any subdirectory is part of a workspace path

    Args:
        path (str): The path to search for an associated group

    Returns:
        str: The group, or None if no group is found.
    """
    workspaces = get_workspaces()
    current_workspace = workspaces.longest_prefix(path)
    if current_workspace:
        return current_workspace.value
    else:
        return None

def add_workspace(path: str, group: str) -> bool:
    """Adds a path as a new workspace associated with the group.

    Args:
        path (str): The path of the workspace
        group (str): The group of the workspace
    """
    workspaces = get_workspaces()
    if workspaces.has_key(path):
        # Can't add a workspace if it already exists!
        return False
    workspace_file = utils.get_config_fname('workspace_path')
    os.makedirs(os.path.dirname(workspace_file), exist_ok=True)
    with open(workspace_file, 'a') as f:
        f.write(f'{path},{group}\n')
    return True

def remove_workspace(path: str) -> bool:
    """Removes a workspace for the given path

    Args:
        path (str): The path of the workspace
    """
    workspaces = get_workspaces()
    deleted_workspace = workspaces.longest_prefix(path)
    if deleted_workspace:
        workspaces.pop(deleted_workspace.key)
        workspace_file = utils.get_config_fname('workspace_path')
        os.makedirs(os.path.dirname(workspace_file), exist_ok=True)
        data = ''.join(f'{path}\n' for path, value in workspaces.items())
        with open(workspace_file, 'w') as f:
            f.write(data)
        return True
    else:
        return False

import os
from typing import List
import pickle

#-------------------------------------------------------------------------------
# Main functions
#-------------------------------------------------------------------------------
def subfiles(
    folder: str, join: bool = True, prefix: str = None, suffix: str = None, sort: bool = True
) -> List[str]:
    """Get the subfiles of a given folder.

    Args:
        folder (str): parent folder used.
        join (bool, optional): Whether to join the folder path. Defaults to True.
        prefix (str, optional): returns files that contains this prefix. Defaults to None.
        suffix (str, optional): returns files that contains this suffix. Defaults to None.
        sort (bool, optional): Whether to sort the list of files. Defaults to True.

    Returns:
        List[str]: Subfiles.
    """
    if join:
        l = os.path.join  # noqa: E741
    else:
        l = lambda x, y: y  # noqa: E731, E741
    res = [
        l(folder, i)
        for i in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, i))
        and (prefix is None or i.startswith(prefix))
        and (suffix is None or i.endswith(suffix))
    ]
    if sort:
        res.sort()
    return res


def subfiles_recursive(
    folder: str, join: bool = True, prefix: str = None, suffix: str = None, sort: bool = True
) -> List[str]:
    """Get the subfiles in all the child directories of a given folder.

    Args:
        folder (str): parent folder used.
        join (bool, optional): Whether to join the folder path. Defaults to True.
        prefix (str, optional): returns files that contains this prefix. Defaults to None.
        suffix (str, optional): returns files that contains this suffix. Defaults to None.
        sort (bool, optional): Whether to sort the list of files. Defaults to True.

    Returns:
        List[str]: Subfiles.
    """
    
    files = []
    for dirpath, _, _ in os.walk(folder):
        files+=subfiles(dirpath, join, prefix, suffix, False)
    if sort:
        files.sort()
    return files


def subdirs(
    folder: str, join: bool = True, prefix: str = None, suffix: str = None, sort: bool = True
) -> List[str]:
    """Get the subdirs of a given folder.

    Args:
        folder (str): parent folder used.
        join (bool, optional): Whether to join the folder path. Defaults to True.
        prefix (str, optional): returns files that contains this prefix. Defaults to None.
        suffix (str, optional): returns files that contains this suffix. Defaults to None.
        sort (bool, optional): Whether to sort the list of files. Defaults to True.

    Returns:
        List[str]: Subfiles.
    """
    if join:
        l = os.path.join  # noqa: E741
    else:
        l = lambda x, y: y  # noqa: E731, E741
    res = [
        l(folder, i)
        for i in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, i))
        and (prefix is None or i.startswith(prefix))
        and (suffix is None or i.endswith(suffix))
    ]
    if sort:
        res.sort()
    return res


def load_pickle(path):
    return pickle.load(open(path, 'rb'))

def save_pickle(obj, path):
    pickle.dump(obj, open(path, 'wb'))
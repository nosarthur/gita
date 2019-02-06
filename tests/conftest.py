import os

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PATH_FNAME = os.path.join(TEST_DIR, 'mock_path_file')
PATH_FNAME_EMPTY = os.path.join(TEST_DIR, 'empty_path_file')
PATH_FNAME_CLASH = os.path.join(TEST_DIR, 'clash_path_file')
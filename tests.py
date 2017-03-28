"""Basic testing for google drive uploader. This will upload repo
files to a folder named 'test' in the connected google drive account.
"""

from __future__ import print_function

import os

import driveuploader


home = os.path.split(os.path.realpath(__name__))[0]


# clean up old tests, empty gdrive test folder
ul = driveuploader.Uploader(file_list="README.md",
                            mimetype='text/plain',
                            home_dir=home,
                            description="Test file",
                            folder="test")

test_folder_id = ul.find_folder()




# test upload functionality

# test upload backup

# test upload no-overwrite

# test upload file exists

# test upload force

# make bash script for testing args
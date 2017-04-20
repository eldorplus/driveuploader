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

files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id)").execute()['files']

file_ids = [x['id'] for x in files]

for file_id in file_ids:
    ul.service.files().update(
        fileId=file_id,
        body={
            'trashed': True
        }
    ).execute()

files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id)").execute()['files']

assert len(files) == 0  # Make sure test folder is empty

# test upload functionality
ul.upload()
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, properties, description)").execute()['files']
assert len(files) == 1  # Test folder should have one file
assert files[0]['properties']['modified']  # file should have custom property
assert files[0]['description'] == "Test file"  # file should have description

# test upload backup
ul.backup = True
ul.upload(force=True)
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, properties)").execute()['files']
assert len(files) == 2  # Test folder should have two files
no_overwrites = 0
for file in files:
    if file['properties'].get('no_overwrite') == 'true':
        no_overwrites += 1
assert no_overwrites == 1  # Backup file should have 'no_overwrite' property

# test upload no-overwrite
ul.backup = False
ul.no_overwrite = True
ul.upload()
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, properties)").execute()['files']
assert len(files) == 3  # Test folder should have three files
no_overwrites = 0
for file in files:
    if file['properties'].get('no_overwrite') == 'true':
        no_overwrites += 1
assert no_overwrites == 2  # newest file should have 'no_overwrite'

# test upload file exists
ul.no_overwrite = False
ul.upload()
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, description)").execute()['files']
assert len(files) == 3  # Upload should fail, still only 3 files

# test upload force
descs = []
for file in files:
    descs.append(file['description'])
assert len(set(descs)) == 1  # all files should have same description
ul = driveuploader.Uploader(file_list="README.md",
                            mimetype='text/plain',
                            home_dir=home,
                            description="Test2",
                            folder="test")
ul.upload(force=True)
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, description)").execute()['files']
assert len(files) == 3  # Test folder should still have 3 files
descs = []
for file in files:
    descs.append(file['description'])
assert len(set(descs)) == 2  # overwritten file should have different description
print("Tests passed.")
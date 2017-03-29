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

assert len(files) == 0

# test upload functionality
ul.upload()
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, properties, description)").execute()['files']
assert len(files) == 1
assert files[0]['properties']['modified']
assert files[0]['description'] == "Test file"

# test upload backup
ul.backup = True
ul.upload(force=True)
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, properties)").execute()['files']
assert len(files) == 2
no_overwrites = 0
for file in files:
    if file['properties'].get('no_overwrite') == 'true':
        no_overwrites += 1
assert no_overwrites == 1

# test upload no-overwrite
ul.backup = False
ul.no_overwrite = True
ul.upload()
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, properties)").execute()['files']
assert len(files) == 3
no_overwrites = 0
for file in files:
    if file['properties'].get('no_overwrite') == 'true':
        no_overwrites += 1
assert no_overwrites == 2

# test upload file exists
ul.no_overwrite = False
ul.upload()
files = ul.service.files().list(
    q="'{}' in parents and trashed=false and not mimeType='{}'".format(
        test_folder_id, driveuploader.FOLDER_MIMETYPE),
    fields="files(id, description)").execute()['files']
assert len(files) == 3

# test upload force
descs = []
for file in files:
    descs.append(file['description'])
assert len(set(descs)) == 1
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
descs = []
for file in files:
    descs.append(file['description'])
assert len(set(descs)) == 2
print("Tests passed.")
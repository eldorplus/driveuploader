"""This module uploads Cogmind save files to Google Drive.

It was made to function on double click rather than via command line
for convenience.

To force upload, import this module and run main(True).
"""

import httplib2
import os

from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# Taken from https://developers.google.com/drive/v3/web/quickstart/python
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Drive API'


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if SCRIPT_DIR !=  os.getcwd():
    os.chdir(SCRIPT_DIR)
os.chdir(os.path.join('..', 'user'))
CM_USER_DIR = os.getcwd()
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

# Add 'cogmind.cfg' to file list to transfer game settings.
USER_FILE_LIST = ['buffer.txt', 'game.bin', 'save.bin', 'tutorial.bin']


# Taken from https://developers.google.com/drive/v3/web/quickstart/python
def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.join(SCRIPT_DIR, 'credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'cmdrive_credentials.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def find_cm_folder(service):
    """Return the Cogmind folder in Google Drive.
    If the folder file is not located, create it.
    """
    cm_folder = service.files().list(
        q="mimeType='{}' and name='cogmind'".format(FOLDER_MIMETYPE),
        spaces='drive').execute()['files']
    if not cm_folder:
        return make_cm_folder(service)['id']
    else:
        return cm_folder[0]['id']

def make_cm_folder(service):
    """Create Google Drive Cogmind folder."""
    file_metadata = {
        'name': 'cogmind',
        'mimeType': FOLDER_MIMETYPE
    }
    file = service.files().create(
        body=file_metadata,
        fields='files(id, name, properties)').execute()
    print 'cogmind folder created, ID: {}'.format(file.get('id'))
    return {'file': file, 'id': file.get('id')}

def find_drive_file(service, filename, folder_id):
    """Return a list of files named'filename' if 'folder_id' is a
    parent folder. Return empty list if none are found.
    """
    file = service.files().list(
        q="'{}' in parents and name='{}' and trashed=false".format(
            folder_id, filename),
        fields="files(id, name, properties)").execute()['files']
    return file

def main(force):
    """Upload cogmind user files to GDrive. Only overwrite existing
    files if they were more recently modified, or if force == True.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    folder_id = find_cm_folder(service)
    
    for filename in USER_FILE_LIST:
        filepath = os.path.join(CM_USER_DIR, filename)
        file_last_update = int(os.path.getmtime(filepath))
        file_metadata = {
            'name': filename,
            'properties': {'modified': file_last_update}
        }
        file_found = find_drive_file(service, filename, folder_id)
        if file_found:
            if not force:
                try:
                    modified = int(file_found[0]['properties']['modified'])
                except KeyError:
                    print "Properties not defined. Use force upload."
                    continue
                if modified > file_last_update:
                    print ("File {} was last modified after local file. FILE "
                    "WAS NOT UPDATED!!! Force upload "
                    "required.").format(filename)
                    continue
                elif modified == file_last_update:
                    print ("File {} has same last modified date. FILE WAS NOT "
                        "UPDATED!!! Force upload required.").format(filename)
                    continue
            media = MediaFileUpload(filepath,
                                    mimetype='text/plain')
            file = service.files().update(
                fileId=file_found[0]['id'],
                media_body=media,
                body=file_metadata
                ).execute()
            print "File {} updated.".format(filepath)
            continue
        file_metadata['parents'] = [ folder_id ]
        media = MediaFileUpload(filepath,
                                mimetype='text/plain')
        file = service.files().create(
            body=file_metadata,
            media_body=media).execute()
        print "File {} uploaded.".format(filepath)
    raw_input()


if __name__ == '__main__':
    main(False)
    raw_input()












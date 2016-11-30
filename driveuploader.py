"""This module uploads files to Google Drive.

If the file already exists (in that folder, if selected) it will
overwrite it only if the modified date in the drive is older than the
modified date of file to be uploaded, unless --force is set.

This module uses a custom 'modified date' property in drive file's
metadata, so manually uploaded files must be forced.
"""
from __future__ import print_function

import argparse
import httplib2
import os
import time

from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Drive API'
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

SCRIPT_DIR = os.path.split(os.path.realpath(__file__))[0]


# Taken from https://developers.google.com/drive/v3/web/quickstart/python
def get_credentials(script_dir):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    :type script_dir: str

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.join(script_dir, 'credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'cmdrive_credentials.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        secret_file = os.path.join(script_dir, CLIENT_SECRET_FILE)
        flow = client.flow_from_clientsecrets(secret_file, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


class Uploader(object):
    """Uploader class. Properties are set with command line args."""

    def __init__(self,
                 folder=None,
                 mimetype=None,
                 home_dir=None,
                 no_overwrite=False,
                 description=None,
                 **kwargs):
        self.file_list = kwargs['file_list'].split(',')
        if folder:
            self.drive_folder = folder
        else:
            self.drive_folder = "root"
        if mimetype:
            self.mimetype = mimetype
        else:
            self.mimetype = None
        self.home_dir = home_dir
        self.no_overwrite = no_overwrite
        self.description = description
        credentials = get_credentials(SCRIPT_DIR)
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=http)

    def find_folder(self):
        """Return the requested folder in Google Drive.
        If the folder file is not located, create it.
        """
        if self.drive_folder == "root":
            return self.drive_folder
        folder = self.service.files().list(
            q="mimeType='{}' and name='{}' "
              "and trashed=false".format(FOLDER_MIMETYPE,
                                         self.drive_folder),
            spaces='drive').execute()['files']
        if not folder:
            return self.make_folder(self.drive_folder)['id']
        else:
            return folder[0]['id']

    def make_folder(self, folder_name):
        """Create Google Drive folder.

        :type folder_name: str
        """
        file_metadata = {
            'name': folder_name,
            'mimeType': FOLDER_MIMETYPE
        }
        folder = self.service.files().create(
            body=file_metadata).execute()
        print('{} folder created, ID: {}'.format(folder_name,
                                                 folder.get('id')))
        return {'file': folder, 'id': folder.get('id')}

    def find_drive_files(self, filename, folder_id):
        """Return a list of files named filename if 'folder_id' is a
        parent folder. Return empty list if none are found. Currently
        only the first file is used.

        :type filename: str
        :type folder_id: str
        """
        no_overwrite_property = "{ key='no_overwrite' and value='true'}"
        files = self.service.files().list(
            q="'{}' in parents and name='{}' and trashed=false and not "
              "mimeType='{}' and not properties has {}".format(
                folder_id, filename, FOLDER_MIMETYPE, no_overwrite_property),
            fields="files(id, name, properties, "
                   "description)").execute()['files']
        return files[0] if files else None

    def upload(self, force=False, check=False):
        """Upload files to GDrive. Only overwrite existing files if
        they were more recently modified, or if force == True.

        :type force: bool
        """
        for local_file in self.file_list:
            filename = os.path.split(local_file)[-1]
            if self.home_dir:
                filepath = os.path.join(self.home_dir, local_file)
            else:
                filepath = os.path.join(SCRIPT_DIR, local_file)
            file_last_update = int(os.path.getmtime(filepath))
            file_metadata = {
                'name': filename,
                'properties': {'modified': file_last_update}
            }
            folder_id = self.find_folder()
            file_found = self.find_drive_files(filename, folder_id)
            if file_found and not self.no_overwrite:
                if not force:
                    try:
                        modified = int(file_found['properties']['modified'])
                    except KeyError:
                        print("Properties not defined for {}. Use force "
                              "upload.".format(filename))
                        if check:
                            print(parse_check(file_last_update,
                                              None,
                                              filename))
                        continue
                    if modified > file_last_update:
                        print("File {} was last modified after local file. "
                               "FILE WAS NOT UPDATED!!! Force upload "
                               "required.".format(filename))
                        if check:
                            print(parse_check(file_last_update,
                                              modified,
                                              filename))
                        continue
                    elif modified == file_last_update:
                        print("File {} has same last modified date. FILE WAS "
                               "NOT UPDATED!!! Force upload "
                               "required.".format(filename))
                        if check:
                            print(parse_check(file_last_update,
                                              modified,
                                              filename))
                        continue

                if check:
                    print("File {} is ready to upload.".format(filename))
                    print(parse_check(file_last_update, modified, filename))
                    continue
                if self.description:
                    file_metadata['description'] = self.description
                media = MediaFileUpload(filepath,
                                        mimetype=self.mimetype)
                self.service.files().update(
                    fileId=file_found['id'],
                    media_body=media,
                    body=file_metadata
                ).execute()
                print("File {} updated.".format(filepath))
                continue

            if check:
                print("File {} does not exist in GDrive. Ready to "
                      "upload.".format(filename))
                print(parse_check(file_last_update, None, filename))
                continue
            if self.description:
                file_metadata['description'] = self.description
            if self.no_overwrite:
                file_metadata['properties']['no_overwrite'] = 'true'
            file_metadata['parents'] = [ folder_id ]
            media = MediaFileUpload(filepath,
                                    mimetype=self.mimetype)
            self.service.files().create(
                body=file_metadata,
                media_body=media).execute()
            print("File {} uploaded.".format(filepath))


def parse_check(local_update, drive_update, filename):
    """Parse strings for printing information for 'check' option."""
    time_string = "%Y-%m-%d, %H:%M:%S"
    local_mod_time = time.strftime(time_string,
                                   time.localtime(local_update))
    if drive_update:
        drive_mod_time = time.strftime(time_string,
                                       time.localtime(drive_update))
    else:
        drive_mod_time = "Undefined"
    return ("{}:\n  Local file last updated: {}\n  Remote file last updated: "
        "{}").format(filename, local_mod_time, drive_mod_time)


def main(check=False, force=False, **kwargs):
    gdrive = Uploader(**kwargs)
    if check:
        gdrive.upload(check=True)
    elif force:
        gdrive.upload(force=True)
    else:
        gdrive.upload()


if __name__ == '__main__':

    arg_help = [
        "Save or overwrite files to Google Drive. The last modified date of "
            "the file is written to a custom property, and will only overwrite"
            " without --force if this date is before the file's last modified "
            "date.",
        "Files list separated by comma (no spaces, use quotes). (required).",
        "Home directory to look for items in file_list. If omitted include the"
            " full path in the file list or relative path to script will be "
            "used.",
        "Folder name to upload files to in Google Drive. If omitted, files "
            "will be placed in root directory.",
        "Force overwrite.",
        "Prints last modified dates and whether 'force' is required to "
            "upload.",
        "Set the mimetype for all files to be uploaded. Generally, Google "
            "Drive handles this automatically. Use 'text/plain' to force a "
            "file to work with Drive editors like Drive Notepad.",
        "Set a description to all files to be uploaded, visible in GDrive "
            "app (use quotes). Use --description=\" \" to remove description.",
        "Add files without overwriting. 'no_overwrite' files will be flagged "
            "with a custom property and will never be found by the script.",
        "Enables the 'Press enter to close.' prompt at script end."
    ]

    parent = tools.argparser
    group = parent.add_argument_group('standard')
    exclusive_group = parent.add_mutually_exclusive_group()
    parent.add_argument("file_list", help=arg_help[1])
    parent.add_argument("-d", "--home_dir", help=arg_help[2])
    parent.add_argument("--folder", help=arg_help[3])
    exclusive_group.add_argument("--force",
                                 help=arg_help[4],
                                 action='store_true')
    exclusive_group.add_argument("-c",
                                 "--check",
                                 help=arg_help[5],
                                 action='store_true')
    parent.add_argument("--mimetype", help=arg_help[6])
    parent.add_argument("--description", help=arg_help[7])
    parent.add_argument("--no_overwrite",
                        help=arg_help[8],
                        action='store_true')
    parent.add_argument("--prompt",
                        help=arg_help[9],
                        action='store_true')
    flags = argparse.ArgumentParser(
        parents=[parent],
        description=arg_help[0]
    ).parse_args()
    kw_args = vars(flags)

    main(**kw_args)
    if kw_args['prompt']:
        raw_input("Press enter to close.")












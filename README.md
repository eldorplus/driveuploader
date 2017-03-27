# Google Drive Uploader

Uploads files to Google Drive. By default it checks if the files exist, and checks for a 'last modified' custom property in the drive file's metadata. If the last modified date is the same or later than the last modified date of the local file (or doesn't exist, if you manually uploaded the file), it requires the --force option to upload.

It is meant to be used with batch files to keep uploaded GDrive files updated without needing to delete the old ones and replace the new ones, as well as preventing uploads from replacing a newer revision of the file. I'll eventually add a similar functioning GDrive file downloader.

## Requirements:

You need Google Drive API credentials to access the API for uploading files. See here: https://developers.google.com/drive/v3/web/quickstart/python. This script looks for it in the same folder with the name 'client_secret.json'.

Install required library: `pip install -r C:\path\to\requirements.txt`

## Args:

Omitted default GDrive API options here for brevity.

```
usage: driveuploader.py [-h]
                        [-d HOME_DIR] [--folder FOLDER] [--force | -c]
                        [--mimetype MIMETYPE] [--description DESCRIPTION]
                        [--no_overwrite] [--prompt]
                        file_list

Save or overwrite files to Google Drive. The last modified date of the file is
written to a custom property, and will only overwrite without --force if this
date is before the file's last modified date.

positional arguments:
  file_list             Files list separated by comma (no spaces, use quotes).
                        (required).

optional arguments:
  -h, --help            show this help message and exit
  -d HOME_DIR, --home_dir HOME_DIR
                        Home directory to look for items in file_list. If
                        omitted include the full path in the file list or
                        relative path to script will be used.
  --folder FOLDER       Folder name to upload files to in Google Drive. If
                        omitted, files will be placed in root directory.
  --force               Force overwrite.
  -c, --check           Prints last modified dates and whether 'force' is
                        required to upload.
  --mimetype MIMETYPE   Set the mimetype for all files to be uploaded.
                        Generally, Google Drive handles this automatically.
                        Use 'text/plain' to force a file to work with Drive
                        editors like Drive Notepad.
  --description DESCRIPTION
                        Set a description to all files to be uploaded, visible
                        in GDrive app (use quotes). Use --description=" " to
                        remove description.
  --no_overwrite        Add files without overwriting. 'no_overwrite' files
                        will be flagged with a custom property and will never
                        be found by the script.
  --prompt              Enables the 'Press enter to close.' prompt at script
                        end.
```

## Batch:
A simple batch files/example commands:

upload_myfiles.bat:
```
python C:\Users\Username\Desktop\driveuploader.py "file.txt,otherfile.txt,data.bin" -d "C:\Path\To\Folder" --folder gdrivefolder
```

force_upload.bat:
```
python C:\Users\Username\Desktop\driveuploader.py "C:\Path\To\Folder\file.txt,C:\Path\To\Folder\otherfile.txt,C:\Path\To\Folder\data.bin" --force
```

## Etc:

I noticed while uploading multiple files with `--no_overwrite` that the files may not show in the order of upload in Google Drive. So if you have multiple of the same file in the same folder, it may be difficult to determine which is no_overwrite or not. Sadly the custom file property metadata doesn't seem to be accessible from the Drive app, so setting the file's description via `--description` may be necessary.
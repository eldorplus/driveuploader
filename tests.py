from __future__ import print_function

import os

import driveuploader


home = os.path.split(os.path.realpath(__name__))[0]
testfile = "README.md"

ul = driveuploader.Uploader(file_list="README.md",
                            mimetype='text/plain',
                            home_dir=home)

ul.upload(check=True)

print("")
print("Basic upload check test passed.")

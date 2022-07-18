# Vulnerable Task Manager

""" misc.py contains miscellaneous functions

    Functions that are used in multiple places in the
    rest of the application, but are not tied to a
    specific area are stored in misc.py
"""

import os


def store_uploaded_file(title, uploaded_file):
    """ Stores a temporary uploaded file on disk """
    upload_dir_path = '%s/static/taskManager/uploads' % (
        os.path.dirname(os.path.realpath(__file__)))
    if not os.path.exists(upload_dir_path):
        os.makedirs(upload_dir_path)

    # Let's avoid the file corruption race condition!
    os.system(
        "mv " +
        uploaded_file.temporary_file_path() +
        " " +
        "%s/%s" %
        (upload_dir_path,
         title))

    return '/static/taskManager/uploads/%s' % (title)

def store_url_data(url, _file):
    """ Stores a temporary uploaded file on disk """
    upload_dir_path = '%s/static/taskManager/uploads' % (
        os.path.dirname(os.path.realpath(__file__)))
    if not os.path.exists(upload_dir_path):
        os.makedirs(upload_dir_path)

    filename = url.split("/")[-1].split("?")[0]

    with open("%s/%s" % (upload_dir_path,filename), 'wb') as f:
        f.write(_file)

    return '/static/taskManager/uploads/%s' % (filename)

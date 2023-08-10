import mimetypes
import os
import shutil
import tempfile

from odoo.tools.mimetypes import guess_mimetype


def check_name(name):
    tmp_dir = tempfile.mkdtemp()
    try:
        open(os.path.join(tmp_dir, name), "a").close()
    except IOError:
        return False
    finally:
        shutil.rmtree(tmp_dir)
    return True


def compute_name(name, suffix, escape_suffix):
    if escape_suffix:
        name, extension = os.path.splitext(name)
        return "{}({}){}".format(name, suffix, extension)
    else:
        return "{}({})".format(name, suffix)


def unique_name(name, names, escape_suffix=False):
    if not name in names:
        return name
    else:
        suffix = 1
        name = compute_name(name, suffix, escape_suffix)
        while name in names:
            suffix += 1
            name = compute_name(name, suffix, escape_suffix)
        return name


def unique_files(files):
    ufiles = []
    unames = []
    for file in files:
        uname = unique_name(file[0], unames, escape_suffix=True)
        ufiles.append((uname, file[1]))
        unames.append(uname)
    return ufiles


def guess_extension(filename=None, mimetype=None, binary=None):
    extension = filename and os.path.splitext(filename)[1][1:].strip().lower()
    if not extension and mimetype:
        extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
    if not extension and binary:
        mimetype = guess_mimetype(binary, default="")
        extension = mimetypes.guess_extension(mimetype)[1:].strip().lower()
    return extension


def ensure_path_directories(path):
    directory_path = os.path.dirname(path)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def remove_empty_directories(path):
    if not os.path.isdir(path):
        return
    entries = os.listdir(path)
    if len(entries) > 0:
        for entry in entries:
            subpath = os.path.join(path, entry)
            if os.path.isdir(subpath):
                self._remove_empty_directories(subpath)
    else:
        os.rmdir(path)

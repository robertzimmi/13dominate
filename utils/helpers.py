import os

ALLOWED_EXTENSIONS = {'.csv'}

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

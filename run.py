import os
from notes import app

myapp = app

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	myapp.run()


from notes.models import Note, User
from notes import db


from notes import db
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime


class TimestampMixin:
    created = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)


class Note(TimestampMixin, db.Model):
	__tablename__ = 'note'
	id = db.Column(db.Integer, primary_key=True)
	url_id = db.Column(db.String(9), unique=True, nullable=False)
	title = db.Column(db.String(100))
	text = db.Column(db.Text)

	def __repr__(self):
		return '{}th note {}'.format(self.id, self.url_id)


class User(UserMixin, db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(30), unique=True, nullable=False)
	email = db.Column(db.String(50))
	_password_hash = db.Column('password_hash', db.String(128), nullable=False)

	@hybrid_property
	def password_hash(self):
		return self._password_hash

	@password_hash.setter
	def password(self, password):
		self._password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self._password_hash, password)

	def __repr__(self):
		return '{}th user {}'.format(self.id, self.username)


class UserNoteParams(db.Model):
	__tablename__ = 'user_note_params'
	id = db.Column(db.Integer, primary_key=True)
	note_id = db.Column(db.Integer, db.ForeignKey('note.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	change_possibility = db.Column(db.Boolean)
	private_access = db.Column(db.Boolean)
	encryption = db.Column(db.Boolean)
	# one to one
	user = db.relationship('User', backref=db.backref('user_note_params'), uselist=False)
	# many to one
	note = db.relationship('Note', backref='user_note_params')


class PrivateAccess(db.Model):
	__tablename__ = 'private_access'
	id = db.Column(db.Integer, primary_key=True)
	note_id = db.Column(db.Integer, db.ForeignKey('note.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	# many to one
	user = db.relationship('User', backref='private_accesses')
	# one to one
	note = db.relationship('Note', backref=db.backref('private_access'), uselist=False)


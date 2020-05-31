import os
from credentials import (
	DB_DIALECT, DB_LOGIN, DB_PASSWORD, DB_HOST, DB_NAME
)


class Config:
	DEBUG = True
	SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(16)
	SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}/{}'.format(
					DB_DIALECT, DB_LOGIN, DB_PASSWORD, DB_HOST, DB_NAME)
	SQLALCHEMY_TRACK_MODIFICATIONS = False

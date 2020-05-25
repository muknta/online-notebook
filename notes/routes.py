from flask import render_template, redirect, url_for, flash, jsonify
from flask_login import (
	LoginManager,
	current_user, login_user, logout_user, login_required
)
from notes import app, db
from .models import User, Note, UserNoteParams
from .forms import (
		NoteForm,
		UserForm,
		UserNoteParamsForm,
		RegisterForm,
		LoginForm
	)
from secrets import choice as sec_choice
from string import digits, ascii_letters
from urllib.parse import quote, unquote


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


# decorator for route percent-encoding
def quote_kw_args(function):
	def wrap_fun(*args, **kwargs):
		upd_kwargs = dict(zip(kwargs, map(quote, kwargs.values())))
		upd_args = map(quote, args)
		return function(*upd_args, **upd_kwargs)
	return wrap_fun


def get_user_by_username(username):
	return User.query.filter_by(username=username).first()

def get_note_by_url_id(url_id):
	return Note.query.filter_by(url_id=url_id).first()

def get_params_by_fk(note_id, user_id):
	return UserNoteParams.query.filter_by(
					note_id=note_id,
					user_id=user_id).first()


def db_session_add(new_elem, message=''):
	try:
		db.session.add(new_elem)
		db.session.commit()
		flash(message)
	except:
		db.session.rollback()


def db_session_delete(query, del_id, message=''):
	try:
		del_item = db.session.query(query).get(del_id)
		db.session.delete(del_item)
		db.session.commit()
		flash(message)
	except:
		db.session.rollback()


@app.route('/')
def index():
	#check by parameters if public
	return render_template('index.html')


def generate_url_id():
	alphabet = digits + ascii_letters.upper() + ascii_letters
	url_id = ''.join(sec_choice(alphabet) for i in range(10))
	return url_id


@app.route('/create')
def note_create():
	new_url_id = generate_url_id()
	new_note = Note(url_id=new_url_id)
	message = '{}th note'.format(new_note.id)
	db_session_add(new_note, message)

	if current_user.is_authenticated:
		params = get_params_by_fk(new_note.id, current_user.id)
		db_session_add(params)	

	return redirect(url_for('note_edit', url_id=new_url_id))


@app.route('/edit/<string:url_id>', methods=['GET', 'POST'])
def note_edit(url_id):
	note = get_note_by_url_id(url_id)
	if not note:
		return jsonify('404: Not Found'), 404

	params_form = None
	note_form = NoteEditForm(request.POST, obj=note)
	if current_user.is_authenticated:
		params = get_params_by_fk(note.id, current_user.id)
		if params:
			params_form = UserNoteParamsForm(request.POST, obj=params)
			params_form.access.default = 'private' if params.private_access else 'public'
	if note_form.validate_on_submit():
		if params_form:
			params.private_access = True if params_form.access.default == 'private' else False
		db.session.commit()

	return render_template('note_edit.html', note_form=note_form, params_form=params_form)


@app.route('/view/<string:url_id>')
def note_view(url_id):
	note = get_note_by_url_id(url_id)
	if not note:
		return jsonify('404: Not Found'), 404
	params = UserNoteParams.query.filter_by(note_id=note_id).first()
	if params:
		pass

	return render_template('note_view.html', note=note, params=params)


@app.route('/view/<string:url_id>/delete')
def note_delete(url_id):
	return render_template('note_view.html')


@app.route('/user/<string:username>')
@quote_kw_args
def user_notes(username):
	user = get_user_by_username(username)
	if not user:
		return jsonify('404: Not Found'), 404
	params = UserNoteParams.query.filter_by(user_id=user.id)
	notes = []
	for param in params:
		notes.append(Note.query.get(param.note_id))
	return render_template('user_notes.html', notes=notes)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	user = User.query.get(current_user.id)
	form = UserForm(user)
	if form.validate_on_submit():
		flash('Information updated')
		db.session.commit()
		return redirect(url_for('profile'))

	return render_template('profile.html', form=form)


@app.route('/profile/delete')
@login_required
def profile_delete(url_id):
	return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('profile'))
	form = LoginForm()

	if form.validate_on_submit():
		user = get_user_by_username(form.username.data)
		if user:
			if user.check_password(form.password.data):
				login_user(user, remember=form.remember_me.data)

				flash('Entered as user "{}", remember_me={}'.format(
					form.username.data, form.remember_me.data))
				return redirect(url_for('profile'))
		flash('Invalid username or password')
	return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('profile'))
	form = RegisterForm()

	if form.validate_on_submit():
		if get_user_by_username(form.username.data):
			flash('User "{}" already exist'.format(form.username.data))
			return redirect(url_for('register'))
		else:
			new_user = User(username=form.username.data,
							password_hash=form.password.data,
							email=form.email.data)

			message = 'Sign Up requested for user "{}"'.format(form.username.data)
			db_session_add(new_user, message)

			return redirect(url_for('login'))
	elif form.submit.data and not form.validate_on_submit():
		flash('Fill the fields. NEED TO BE IN WTFORMS')
		return redirect(url_for('register'))
	return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


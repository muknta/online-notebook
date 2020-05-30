from flask import (
	render_template, redirect, request, url_for, flash, jsonify
)
from flask_login import (
	LoginManager,
	current_user, login_user, logout_user, login_required
)
from notes import app, db
from sqlalchemy import or_
from .models import User, Note, UserNoteParams, PrivateAccess
from .forms import (
		NoteForm,
		UserForm,
		UserNoteParamsForm,
		RegisterForm,
		LoginForm,
		SearchForm
	)
from secrets import choice as sec_choice
from string import digits, ascii_letters
from urllib.parse import quote, unquote
from functools import wraps


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


# decorator for route percent-encoding
def quote_kw_args(function):
	@wraps(function)
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


def db_session_add(new_elem, succ_msg='', err_msg='Some error...'):
	try:
		db.session.add(new_elem)
		db.session.commit()
		if succ_msg:
			flash(succ_msg)
	except:
		if err_msg:
			flash(err_msg)
		db.session.rollback()


def db_session_delete(del_elem, succ_msg='', err_msg='Some error...'):
	try:
		db.session.delete(del_elem)
		db.session.commit()
		if succ_msg:
			flash(succ_msg)
	except:
		if err_msg:
			flash(err_msg)
		db.session.rollback()


@app.route("/chart")
def chart():
	legend = 'Notes Type'
	labels = ['anonymous notes', 'user notes']

	anon_notes_count = db.session.query(Note).join(UserNoteParams, 
					UserNoteParams.note_id == Note.id, isouter=True)\
					.filter(UserNoteParams.id == None).count()
	user_notes_count = db.session.query(UserNoteParams.id).count()
	values = [anon_notes_count, user_notes_count]
	return render_template('chart.html', values=values, labels=labels, legend=legend)


@app.route('/')
def index():
	notes = db.session.query(Note).join(UserNoteParams, 
					UserNoteParams.note_id == Note.id, isouter=True)\
					.join(User, 
					User.id == UserNoteParams.user_id, isouter=True)\
					.add_columns(Note.id, Note.title, Note.url_id,
						Note.created, Note.updated, User.username)\
					.filter(or_(UserNoteParams.id == None,
								UserNoteParams.private_access == False))\
					.order_by(Note.updated.desc())
	
	return render_template('index.html', notes=notes)


@app.route('/search', methods=['GET','POST'])
def search():
	form = SearchForm()
	if request.method == 'POST' and form.submit.data:
		search = "%{}%".format(form.search_query.data)
		notes = db.session.query(Note).join(UserNoteParams, 
						UserNoteParams.note_id == Note.id, isouter=True)\
						.join(User, 
						User.id == UserNoteParams.user_id, isouter=True)\
						.add_columns(Note.id, Note.title, Note.url_id,
							Note.text, Note.updated, User.username)\
						.filter(or_(User.username.like(search),
									Note.title.like(search),
									Note.text.like(search)))\
						.order_by(Note.updated.desc())

		return render_template('search.html', form=form, notes=notes)
	return render_template('search.html', form=form)


def generate_url_id():
	alphabet = digits + ascii_letters.upper() + digits + ascii_letters
	url_id = ''.join(sec_choice(alphabet) for i in range(9))
	return url_id


@app.route('/create')
def note_create():
	new_url_id = generate_url_id()
	new_note = Note(url_id=new_url_id)
	db_session_add(new_note)
	flash('{}th note'.format(new_note.id))

	if current_user.is_authenticated:
		params = UserNoteParams(note_id=new_note.id, user_id=current_user.id,)
		db_session_add(params)	

	return redirect(url_for('note_edit', url_id=new_url_id))


@app.route('/edit/<string:url_id>', methods=['GET', 'POST'])
def note_edit(url_id):
	note = db.session.query(Note).filter_by(url_id=url_id).first()
	if not note:
		return jsonify('404: Not Found'), 404

	params_form = None
	note_form = NoteForm(formdata=request.form, obj=note)
	params = db.session.query(UserNoteParams).filter_by(
										note_id=note.id).first()
	if params:
		if current_user.is_authenticated \
			and params.user_id == current_user.id:
			params_form = UserNoteParamsForm(formdata=request.form, obj=params)
			params_form.access.data = 'private' if params.private_access else 'public'
		else:
			if params.private_access:
				username = User.query.get(params.user_id).username
				return redirect(url_for('user_notes', username=username))
			if not params.change_possibility or params.encryption:
				return redirect(url_for('note_view', url_id=url_id))
	if request.method == 'POST' and note_form.validate_on_submit():
		if params_form:
			params.private_access = True if params_form.access.data == 'private' else False
			params.encryption = params_form.encryption.data
			params.change_possibility = params_form.change_possibility.data
		note.title = note_form.title.data
		note.text = note_form.text.data
		flash('Information updated')
		db.session.commit()
		if note_form.publish.data:
			return redirect(url_for('note_view', url_id=url_id))

	return render_template('note_edit.html', url_id=url_id, note_form=note_form, params_form=params_form)


@app.route('/view/<string:url_id>')
def note_view(url_id):
	note = get_note_by_url_id(url_id)
	if not note:
		return jsonify('404: Not Found'), 404
	params = UserNoteParams.query.filter_by(note_id=note.id).first()
	if params:
		if (current_user.is_authenticated \
				and params.user_id == current_user.id) \
				or not params.private_access:
			return render_template('note_view.html', note=note, params=params)
		else:
			author = User.query.get(params.user_id)
			flash("This note under private control, don't touch that!11)00")
			return redirect(url_for('user_notes', username=author.username))
	return render_template('note_view.html', note=note, params=None)


@app.route('/edit/<string:url_id>/delete')
def note_delete(url_id):
	note = db.session.query(Note).filter_by(url_id=url_id).first()
	params = db.session.query(UserNoteParams).filter_by(note_id=note.id).first()
	if params:
		if not current_user.is_authenticated \
			or params.user_id != current_user.id:
			flash("You have not rights to delete this note!11")
			return redirect(url_for('note_view', url_id=url_id))

	accesses = db.session.query(PrivateAccess).filter_by(note_id=note.id).all()
	for access in accesses:
		db_session_delete(access, err_msg='did not have accesses')
	db_session_delete(note, "{}'th note was deleted".format(note.id))
	
	return redirect(url_for('index'))


@app.route('/user/<string:username>')
@quote_kw_args
def user_notes(username):
	username = unquote(username)
	user = get_user_by_username(username)
	if not user:
		return jsonify('404: Not Found'), 404

	if current_user.is_authenticated \
		and current_user.username == user.username:
		params = UserNoteParams.query.filter_by(user_id=user.id).all()
	else:
		params = UserNoteParams.query.filter_by(
					user_id=user.id, private_access=False).all()
	notes = []
	for param in params:
		notes.append(Note.query.get(param.note_id))
	return render_template('user_notes.html', username=username, notes=notes)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	user = db.session.query(User).get(current_user.id)
	form = UserForm(formdata=request.form, obj=user)
	if request.method == 'POST' and form.validate_on_submit():
		if user.check_password(form.curr_password.data):
			try:
				user.username = form.username.data
				user.email = form.email.data
				if form.new_password.data:
					if len(form.new_password.data) >= 8:
						user.password = form.new_password.data
					else:
						flash('new_password: length must be between 8 and 40')
				db.session.commit()
				flash('Information updated')
				return redirect(url_for('profile'))
			except:
				flash('Some error...')
				db.session.rollback()
		else:
			flash('Current password is not correct')
	elif form.submit.data and not form.validate_on_submit():
		for fieldName, errorMessages in form.errors.items():
			flash('{}: {}'.format(fieldName, errorMessages))

	return render_template('profile.html', form=form)


@app.route('/profile/delete/<int:user_id>')
@login_required
def profile_delete(user_id):
	params = db.session.query(UserNoteParams).filter_by(user_id=user_id).all()
	accesses = db.session.query(PrivateAccess).filter_by(user_id=user_id).all()
	for access in accesses:
		db_session_delete(access, err_msg='did not have accesses')
	for param in params:
		note = db.session.query(Note).get(param.note_id)
		db_session_delete(note,
			err_msg='problem via {}th note deleting'.format(param.note_id))
		db_session_delete(param, err_msg='did not have params')
	user = db.session.query(User).get(user_id)
	db_session_delete(user, "{}'s Profile was deleted".format(user.username))
	
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
			# return redirect(url_for('register'))
		else:
			new_user = User(username=form.username.data,
							password=form.password.data,
							email=form.email.data)

			message = 'Sign Up requested for user "{}"'.format(form.username.data)
			db_session_add(new_user, message)

			return redirect(url_for('login'))
	elif form.submit.data and not form.validate_on_submit():
		flash('{} - {} - {} - {}'.format(form.username.data,form.password.data,form.confirm.data,form.email.data))

	return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


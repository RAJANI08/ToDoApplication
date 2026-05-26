from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin,login_user, login_required,logout_user, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)   # creates flask application

# ---------------- CONFIG ----------------

app.config['SECRET_KEY'] = 'secret-key'   # REQUIRED for login
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost:3306/listtodo_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)    # creates db object that connects SQlAlchemy with Falsk application 

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------- MODELS ----------------

class User(db.Model, UserMixin):
    __tablename__ = "user"   # explicity declaring tableName.....so there will be no confusion w.r.t tableName

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    tasks = db.relationship('ToDoTask', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class ToDoTask(db.Model):
    __tablename__ = "to_do_task"  # explicity declaring tableName.....so there will be no confusion w.r.t tableName


    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# ---------------- LOGIN MANAGER ----------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- ROUTES ----------------

@app.route('/hello')  # decorators maps the URLs path to specific python function
def hello():
    return "hello world !!!!"


@app.route('/')
def home():
    return redirect('/login')


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "User already exists"

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect('/index')

        return "Invalid credentials"

    return render_template('login.html')


# ---------- LOGOUT ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# ---------- TO DO ----------
@app.route('/index', methods=['GET', 'POST'])
@login_required
def ToDo():
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("desc")

        if not title:
            return "Title is required", 400

        todo = ToDoTask(title=title, desc=desc, user_id=current_user.id)

        db.session.add(todo)
        db.session.commit()

        return redirect('/index')

    allTodo = ToDoTask.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', allTodo=allTodo)


# ---------- UPDATE ----------
@app.route('/update/<int:sno>', methods=['GET', 'POST'])
@login_required
def update(sno):
    todo = ToDoTask.query.filter_by(sno=sno,user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        todo.title = request.form['title']
        todo.desc = request.form['desc']
        db.session.commit()
        return redirect('/index')

    return render_template('update.html', todo=todo)


# ---------- DELETE ----------
@app.route('/delete/<int:sno>')
@login_required
def delete(sno):
    todo = ToDoTask.query.filter_by(sno=sno,user_id=current_user.id).first_or_404()

    db.session.delete(todo)
    db.session.commit()
    return redirect('/index')

# ---------- SEARCH ----------

@app.route('/search')
@login_required
def search():
    title = request.args.get('q')

    allTodo = ToDoTask.query.filter(ToDoTask.user_id == current_user.id,ToDoTask.title.ilike(f"%{title}%")).all()

    return render_template('index.html', allTodo=allTodo)

# ---------- ABOUT ----------

@app.route('/about')
def about():
    return render_template('about.html')


# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

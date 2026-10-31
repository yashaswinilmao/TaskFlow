import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tasks = db.relationship("Task", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default="")
    priority = db.Column(db.String(10), default="Medium", nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "taskflow.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        status = request.args.get("status", "all")
        search = request.args.get("q", "").strip()
        query = Task.query.filter_by(user_id=current_user.id)
        if status == "active":
            query = query.filter_by(completed=False)
        elif status == "completed":
            query = query.filter_by(completed=True)
        if search:
            query = query.filter(Task.title.ilike(f"%{search}%"))
        tasks = query.order_by(Task.completed.asc(), Task.created_at.desc()).all()
        total = Task.query.filter_by(user_id=current_user.id).count()
        completed_count = Task.query.filter_by(user_id=current_user.id, completed=True).count()
        return render_template("index.html", tasks=tasks, status=status, search=search,
                               total=total, completed_count=completed_count, today=date.today())

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if len(username) < 3:
                flash("Username must contain at least 3 characters.", "error")
            elif len(password) < 6:
                flash("Password must contain at least 6 characters.", "error")
            elif User.query.filter_by(username=username).first():
                flash("That username is already taken.", "error")
            else:
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Your account is ready. Let's plan your day!", "success")
                return redirect(url_for("index"))
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("index"))
            flash("Incorrect username or password.", "error")
        return render_template("auth.html", mode="login")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/tasks", methods=["POST"])
    @login_required
    def create_task():
        title = request.form.get("title", "").strip()
        if not title:
            flash("Please enter a task title.", "error")
            return redirect(url_for("index"))
        due_raw = request.form.get("due_date", "").strip()
        try:
            due = date.fromisoformat(due_raw) if due_raw else None
        except ValueError:
            due = None
        priority = request.form.get("priority", "Medium")
        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"
        task = Task(title=title[:160], description=request.form.get("description", "").strip(),
                    priority=priority, due_date=due, user_id=current_user.id)
        db.session.add(task)
        db.session.commit()
        flash("Task added!", "success")
        return redirect(url_for("index"))

    @app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
    @login_required
    def toggle_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
        task.completed = not task.completed
        db.session.commit()
        return redirect(url_for("index"))

    @app.route("/tasks/<int:task_id>/delete", methods=["POST"])
    @login_required
    def delete_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "success")
        return redirect(url_for("index"))

    @app.route("/tasks/<int:task_id>/edit", methods=["POST"])
    @login_required
    def edit_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
        title = request.form.get("title", "").strip()
        if title:
            task.title = title[:160]
            task.description = request.form.get("description", "").strip()
            task.priority = request.form.get("priority", "Medium")
            due_raw = request.form.get("due_date", "").strip()
            try:
                task.due_date = date.fromisoformat(due_raw) if due_raw else None
            except ValueError:
                flash("Invalid due date; existing date was kept.", "error")
            db.session.commit()
            flash("Task updated.", "success")
        return redirect(url_for("index"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

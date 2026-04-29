from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
import secrets

app = Flask(__name__)
#генерация случайного секретного ключа при каждом запуске
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 30  # 30 дней для "Запомнить меня"

#запуск Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Страница для перенаправления при попытке доступа без аутентификации
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, id):
        self.id = id
    
    def get_id(self):
        return str(self.id)

#"База данных" пользователей (в реальном проекте должна быть настоящая БД)
users_db = {
    'user': {
        'password': 'qwerty',  # В реальном проекте пароли должны храниться в хешированном виде!
        'id': 1
    }
}

@login_manager.user_loader
def load_user(user_id): #загрузка пользователя по ID
    for username, user_data in users_db.items():
        if user_data['id'] == int(user_id):
            return User(user_id)
    return None

def get_user_by_username(username): #поиск пользователя по имени
    if username in users_db: 
        return User(users_db[username]['id'])
    return None

def verify_password(username, password): #проверка пароля
    if username in users_db and users_db[username]['password'] == password:
        return True
    return False

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/counter')
def counter():
    #инициализируем счетчик, если его нет
    if 'visit_count' not in session:
        session['visit_count'] = 0
    
    #увеличиваем счетчик
    session['visit_count'] = session.get('visit_count', 0) + 1
    
    #получаем общее количество посещений (для текущей сессии)
    count = session['visit_count']
    
    #проверяем, было ли уже приветствие в этой сессии
    first_visit = session.get('first_visit', True)
    if first_visit:
        session['first_visit'] = False
        message = f"Добро пожаловать! Вы посетили страницу {count} раз."
    else:
        message = f"Вы посетили страницу {count} раз."
    
    return render_template('counter.html', count=count, message=message)

@app.route('/login', methods=['GET', 'POST'])
def login(): #главная страница
    #если пользователь уже аутентифицирован, перенаправляем на главную
    if current_user.is_authenticated:
        flash('Вы уже вошли в систему.', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False
        
        #проверка введенных данных
        if verify_password(username, password):
            user = get_user_by_username(username)
            if user:
                login_user(user, remember=remember)
                flash('Вы успешно вошли в систему!', 'success')
                
                #перенаправление на запрошенную страницу (если была)
                next_page = request.args.get('next')
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret(): #секретная страница
    return render_template('secret.html')

#вспомогательная функция для проверки безопасного URL
def is_safe_url(target):
    ref_url = url_for('index', _external=True)
    test_url = url_for('index', _external=True) + target.lstrip('/')
    return test_url.startswith(ref_url)

@app.errorhandler(401)
def unauthorized(e): #обработка ошибки 401
    flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
    return redirect(url_for('login', next=request.path))

@app.route('/clear-session')
def clear_session(): #очистка сессии (счётчик до 0)
    session.clear()
    flash('Сессия очищена!', 'info')
    return redirect(url_for('counter'))

if __name__ == '__main__':
    app.run(debug=True)
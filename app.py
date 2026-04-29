import re
from flask import Flask, render_template, request, make_response

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # для работы с сессиями (если понадобятся)

#заглушка для пользователей (в реальном приложении должна быть БД)
VALID_CREDENTIALS = {
    'admin': 'password123',
    'user': 'userpass'
}

@app.route('/')
def index():
    return render_template('index.html')

#отображение данных запроса
@app.route('/request-info', methods=['GET', 'POST'])
def request_info(): #получаем все данные для отображения
    url_params = request.args.to_dict()  # параметры URL (GET)
    headers = dict(request.headers)  # все заголовки
    cookies = dict(request.cookies)  # все cookie
    form_data = request.form.to_dict() if request.method == 'POST' else {}  # данные формы (POST)
    
    #устанавливаем тестовые cookie при первом посещении
    resp = make_response(render_template(
        'request_info.html',
        url_params=url_params,
        headers=headers,
        cookies=cookies,
        form_data=form_data
    ))
    
    #если cookie еще нет, устанавливаем тестовую
    if not request.cookies.get('test_cookie'):
        resp.set_cookie('test_cookie', 'test_value_' + str(hash(str(request)))[:5])
    
    return resp

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        #для демонстрации просто передаем данные обратно на страницу
        return render_template('request_info.html', 
                             form_data={'username': username, 'password': '*' * len(password)},
                             active_tab='form')
    
    return render_template('login_form.html')

#Форма с обработкой ошибок (номер телефона)
@app.route('/phone', methods=['GET', 'POST'])
def phone_validation():
    result = None
    error = None
    phone_value = ''
    
    if request.method == 'POST':
        phone_value = request.form.get('phone', '').strip()
        
        #проверяем номер телефона
        is_valid, error_message, formatted_phone = validate_phone(phone_value)
        
        if is_valid:
            result = formatted_phone
        else:
            error = error_message
    
    return render_template('phone_form.html', 
                         phone_value=phone_value,
                         result=result, 
                         error=error)

def validate_phone(phone): #проверка на недопустимые символы
    #разрешенные символы: цифры, пробелы, (, ), -, ., +
    allowed_pattern = r'^[0-9\s\(\)\-\+\.]+$'
    if not re.match(allowed_pattern, phone):
        return False, 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.', None
    
    #извлекаем только цифры из номера
    digits = re.sub(r'\D', '', phone)
    
    #проверяем количество цифр
    if len(digits) < 10 or len(digits) > 11:
        return False, 'Недопустимый ввод. Неверное количество цифр.', None
    
    #дополнительная проверка для номеров с 11 цифрами
    if len(digits) == 11:
        if digits[0] not in ['7', '8']:
            return False, 'Недопустимый ввод. Неверное количество цифр.', None
    #для 10 цифр - добавляем 8 в начало для форматирования
    elif len(digits) == 10:
        digits = '8' + digits
    
    #форматируем номер в формат 8-***-***-**-**
    formatted = f"8-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return True, None, formatted

if __name__ == '__main__':
    app.run(debug=True)
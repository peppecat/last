import json
import uuid  # импортируем отдельно
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from datetime import datetime


app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = 'supersecretkey'


# Пути к файлам для хранения данных
USERS_FILE = 'users.json'
REFERRALS_FILE = 'referrals.json'
PROMOCODES_FILE = 'promocodes.json'
REWARDS_FILE = 'rewards.json'
AFFILIATES_FILE = 'affiliates.json'
PARTNERS_FILE = 'partners.json'
PAYMENTS_FILE = 'payments.json'
PRODUCTS_FILE = 'products.json'
CARDS_FILE = 'cards.json'
WHITELIST_FILE = 'whitelist_users.json'  # Новый файл для whitelist

# Загрузка данных из файлов
def load_data():
    global users, referrals, promocodes, rewards, active_bonuses
    global affiliate_users, partners_data, affiliate_payments, products, cards, whitelist_users

    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    try:
        with open(REFERRALS_FILE, 'r') as f:
            referrals = json.load(f)
    except FileNotFoundError:
        referrals = {}

    try:
        with open(PROMOCODES_FILE, 'r') as f:
            promocodes = json.load(f)
    except FileNotFoundError:
        promocodes = {}

    try:
        with open(REWARDS_FILE, 'r') as f:
            rewards = json.load(f)
    except FileNotFoundError:
        rewards = []

    try:
        with open(AFFILIATES_FILE, 'r') as f:
            affiliate_users = json.load(f)
    except FileNotFoundError:
        affiliate_users = []

    try:
        with open(PARTNERS_FILE, 'r') as f:
            partners_data = json.load(f)
    except FileNotFoundError:
        partners_data = []

    try:
        with open(PAYMENTS_FILE, 'r') as f:
            affiliate_payments = json.load(f)
    except FileNotFoundError:
        affiliate_payments = []

    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        products = {}

    try:
        with open(CARDS_FILE, 'r') as f:
            cards = json.load(f)
    except FileNotFoundError:
        cards = []

    try:
        with open(WHITELIST_FILE, 'r') as f:
            whitelist_users = json.load(f)
    except FileNotFoundError:
        whitelist_users = []  # Если файла нет, создаем пустой список

    active_bonuses = []  # Список активных бонусов

# Сохранение данных в файлы
def save_data():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)
    with open(REFERRALS_FILE, 'w') as f:
        json.dump(referrals, f, indent=4)
    with open(PROMOCODES_FILE, 'w') as f:
        json.dump(promocodes, f, indent=4)
    with open(REWARDS_FILE, 'w') as f:
        json.dump(rewards, f, indent=4)
    with open(AFFILIATES_FILE, 'w') as f:
        json.dump(affiliate_users, f, indent=4)
    with open(PARTNERS_FILE, 'w') as f:
        json.dump(partners_data, f, indent=4)
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(affiliate_payments, f, indent=4)
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=4)
    with open(CARDS_FILE, 'w') as f:
        json.dump(cards, f, indent=4)
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(whitelist_users, f, indent=4)  # Сохраняем whitelist в отдельный файл


# Главная страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password1']
        password_confirm = request.form['password2']
        if password != password_confirm:
            flash('The passwords do not match', 'error')
            return render_template('register.html')
        if username in users:
            flash('Username already exists', 'error')
        users[username] = {'password': password,
                            'balance': {'trc20': 0, 'erc20': 0, 'bep20': 0, 'card': 0},
                            'orders': 0,
                            'expenses': 0,
                            'userorders': [],
                            'topups': []
                          }
        save_data()  # Сохраняем данные в файл
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/register/<ref_code>', methods=['GET', 'POST'])
def register_ref(ref_code):
    if ref_code not in referrals:
        return "Реферальная ссылка не найдена", 404

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password1']
        password_confirm = request.form['password2']

        if password != password_confirm:
            flash('The passwords do not match', 'error')
            return render_template('register.html')

        if username in users:
            flash('Username already exists', 'error')

        users[username] = {
            'password': password,
            'balance': {'trc20': 0, 'erc20': 0, 'bep20': 0, 'card': 0},
            'orders': 0,
            'expenses': 0,
            'userorders': [],
            'topups': []
        }

        if username and password:
            referrals[ref_code].append({
                'name': username,
                'deposit': 0,
                'status': 'pending',
                'payout': 0
            })

        save_data()  # Сохраняем данные в файл
        return redirect(url_for('login'))

    return render_template('register.html', ref_code=ref_code)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash("Incorrect username or password!", 'error')  # Добавляем сообщение об ошибке
        return redirect(url_for('login'))  # Перенаправляем обратно на страницу входа
    return render_template('login.html')

# Загрузка данных при старте приложения
load_data()

# Страница для отображения наград
@app.route('/rewards_hub')
def rewardshub():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    return render_template('rewardshub.html', username=username, balances=balances, rewards=rewards, active_bonuses=active_bonuses)



# Страница создания промокодов
@app.route('/admin/promo', methods=['GET', 'POST'])
def create_promo():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403
    if request.method == 'POST':
        key = request.form['key']
        title = request.form['title']
        promo_code = request.form['promo_code']
        hidden = 'hidden' in request.form  # Проверяем, установлен ли чекбокс
        
        # Сохраняем промокод в словарь
        promocodes[key] = {
            'key': promo_code,  # Это будет сам ключ
            'title': title,
            'hidden': hidden,
            'used': False  # Новый флаг, который показывает, активирован ли промокод
        }
        save_data()  # Сохраняем данные в файл
        return redirect(url_for('create_promo'))
    
    return render_template('admin_create_promo.html', promocodes=promocodes)

# Удаление промокода
@app.route('/delete_promo/<key>', methods=['POST'])
def delete_promo(key):
    if key in promocodes:
        del promocodes[key]
        save_data()  # Сохраняем данные в файл
    return redirect(url_for('create_promo'))

# API для проверки, скрытый ли промокод
@app.route('/check_promo/<key>', methods=['GET'])
def check_promo(key):
    if key in promocodes:
        return jsonify({'hidden': promocodes[key]['hidden']})
    return jsonify({'error': 'Promo code not found'}), 404

# Страница активации промокода
@app.route('/activate', methods=['POST'])
def activate():
    promocode = request.form['promoCode']
    
    # Проверка на существование промокода в базе
    if promocode in promocodes:
        bonus = promocodes[promocode]
        
        if not bonus['used']:  # Если промокод еще не был использован
            active_bonuses.append(bonus)
            promocodes[promocode]['used'] = True  # Помечаем как использованный
            save_data()  # Сохраняем данные в файл
        return redirect(url_for('rewardshub'))
    else:
        return "Invalid promo code!", 404

# Страница Admin
@app.route('/admin/users', methods=['GET', 'POST'])
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        action = request.form.get('action')
        target_user = request.form.get('target_user')

        if target_user in users:
            if action == 'edit_balance':
                balance_type = request.form.get('balance_type')
                new_value = float(request.form.get('new_balance'))  # Баланс может быть с плавающей точкой
                if balance_type in users[target_user]['balance']:
                    users[target_user]['balance'][balance_type] = new_value
                elif balance_type in ['orders', 'expenses']:
                    users[target_user][balance_type] = new_value

            elif action == 'edit_topup':
                date = request.form.get('date')
                network = request.form.get('network')
                amount = float(request.form.get('amount'))
                status = request.form.get('status')

                # Преобразуем формат даты на сервере (если это нужно) и добавляем секунды
                try:
                    # Проверяем, есть ли секунды в строке даты. Если нет, добавляем ":00".
                    if len(date) == 16:  # формат вида "YYYY-MM-DD HH:MM"
                        date += ":00"  # Добавляем секунды
                    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass  # В случае ошибок форматирования

                if network == 'BEP20':
                    topup_found = False
                    for topup in users[target_user].get('topups', []):
                        if topup['date'] == date and topup['network'] == network:
                            topup['amount'] = amount
                            topup['status'] = status
                            topup_found = True
                            break

                    if not topup_found:
                        if 'topups' not in users[target_user]:
                            users[target_user]['topups'] = []
                        users[target_user]['topups'].append({
                            'date': date,
                            'network': network,
                            'amount': amount,
                            'status': status
                        })

                    # Обновляем баланс, если статус платежа Success
                    if status == 'Success':
                        users[target_user]['balance']['bep20'] = users[target_user]['balance'].get('bep20', 0) + amount

                # Обработка пополнения для карты (Card)
                elif network == 'Card':
                    topup_found = False
                    for topup in users[target_user].get('topups', []):
                        if topup['date'] == date and topup['network'] == network:
                            topup['amount'] = amount
                            topup['status'] = status
                            topup_found = True
                            break

                    if not topup_found:
                        if 'topups' not in users[target_user]:
                            users[target_user]['topups'] = []
                        users[target_user]['topups'].append({
                            'date': date,
                            'network': network,
                            'amount': amount,
                            'status': status
                        })

                    # Обновляем баланс карты, если статус платежа Success
                    if status == 'Success':
                        users[target_user]['balance']['card'] = users[target_user]['balance'].get('card', 0) + amount

            elif action == 'edit_topup_status':
                date = request.form.get('date')
                network = request.form.get('network')
                new_status = request.form.get('new_status')

                # Преобразуем формат даты на сервере (если это нужно) и добавляем секунды
                try:
                    # Проверяем, есть ли секунды в строке даты. Если нет, добавляем ":00".
                    if len(date) == 16:  # формат вида "YYYY-MM-DD HH:MM"
                        date += ":00"  # Добавляем секунды
                    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass  # В случае ошибок форматирования

                for topup in users[target_user].get('topups', []):
                    if topup['date'] == date and topup['network'] == network:
                        topup['status'] = new_status

                        # Если статус изменился на Success, зачисляем баланс
                        if new_status == 'Success':
                            if network == 'BEP20':
                                users[target_user]['balance']['bep20'] = users[target_user]['balance'].get('bep20', 0) + topup['amount']
                            elif network == 'Card':
                                users[target_user]['balance']['card'] = users[target_user]['balance'].get('card', 0) + topup['amount']
                        break

            elif action == 'delete_user':
                del users[target_user]

            elif action == 'delete_topup':
                date = request.form.get('date')
                network = request.form.get('network')
                users[target_user]['topups'] = [
                    topup for topup in users[target_user].get('topups', [])
                    if not (topup['date'] == date and topup['network'] == network)
                ]

            save_data()

    # Сортировка пополнений по дате, от новой к старой
    for user, info in users.items():
        if 'topups' in info:
            info['topups'] = sorted(
                info['topups'], 
                key=lambda x: x['date'] if x['date'] else "",  # Используем пустую строку для None
                reverse=True
            )

    return render_template('admin_users.html', users=users)







@app.route('/admin/create_code', methods=['POST'])
def create_code():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Получаем данные из формы
    product_id = request.form.get('product_id')
    new_code = request.form.get('new_code')
    
    # Находим категорию по product_id
    category = None
    for key in products:
        if product_id in products[key]:
            category = key
            break

    if category:
        # Добавляем новый код в список "codes"
        if isinstance(products[category][product_id], dict):
            products[category][product_id]["codes"].append(new_code)
        else:
            # Если структура данных отличается, можно создать список
            products[category][product_id] = {
                "description": products[category][product_id],
                "codes": [new_code]
            }

        # Сохраняем изменения в файле products.json
        save_data()

    return redirect(url_for('adminlots'))

@app.route('/admin/delete_code', methods=['POST'])
def delete_code():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Получаем данные из формы
    product_id = request.form.get('product_id')
    code_to_delete = request.form.get('code')
    
    # Находим категорию по product_id
    category = None
    for key in products:
        if product_id in products[key]:
            category = key
            break

    if category and code_to_delete in products[category][product_id]["codes"]:
        # Удаляем код из списка
        products[category][product_id]["codes"].remove(code_to_delete)
        
        # Сохраняем изменения в файл products.json
        save_data()

    return redirect(url_for('adminlots'))



@app.route('/admin/orders', methods=['GET', 'POST'])
def admin2():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403
    
    if request.method == 'POST':
        # Получаем данные из формы для добавления нового заказа
        target_user = request.form.get('target_user')  # Имя пользователя, для которого редактируем заказ
        category = request.form.get('category')
        product = request.form.get('product')
        price = request.form.get('price')
        amount = request.form.get('amount')
        date = request.form.get('date')

        # Преобразуем дату из формата "YYYY-MM-DDTHH:MM" в формат "YYYY-MM-DD HH:MM:SS"
        if date:
            try:
                # Преобразуем строку в объект datetime
                date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M')
                # Форматируем в нужный формат "YYYY-MM-DD HH:MM:SS"
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                formatted_date = None
        else:
            formatted_date = None

        # Если пользователь существует, обновляем его заказы
        if target_user in users:
            # Добавляем новый заказ в начало списка заказов пользователя
            new_order = {
                'category': category,
                'product': product,
                'price': price,
                'amount': amount,
                'date': formatted_date  # Сохраняем отформатированную дату
            }
            # Если заказы еще не существуют у пользователя, создаем пустой список
            if 'userorders' not in users[target_user]:
                users[target_user]['userorders'] = []
            
            # Вставляем заказ в начало списка заказов
            users[target_user]['userorders'].insert(0, new_order)

            save_data()  # Сохраняем данные после изменений
    
    # Сортируем заказы пользователей по дате (новые сверху)
    for user, info in users.items():
        if 'userorders' in info:
            # Сортируем заказы по дате (от более новых к более старым)
            info['userorders'] = sorted(info['userorders'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)

    return render_template('admin_orders.html', users=users)


@app.route('/admin/delete_order/<user>/<int:index>', methods=['POST'])
def delete_order(user, index):
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Удаляем заказ по индексу пользователя
    if user in users and 'userorders' in users[user]:
        orders = users[user]['userorders']
        if 0 <= index < len(orders):
            del orders[index]
            save_data()  # Сохраняем данные после удаления заказа

    return redirect(url_for('admin2'))  # Перенаправление обратно на страницу администрирования

@app.route('/admin/save_key/<user>/<int:index>', methods=['POST'])
def save_key(user, index):
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Получаем введённый ключ из формы
    key = request.form.get('key')

    # Проверяем, существует ли пользователь и заказ
    if user in users and 'userorders' in users[user]:
        if index < len(users[user]['userorders']):
            # Обновляем ключ для указанного заказа
            users[user]['userorders'][index]['key'] = key
            save_data()  # Сохраняем данные после изменений

    return redirect(url_for('admin2'))  # Перезагружаем страницу для отображения обновлений







@app.route('/admin/payments', methods=['GET', 'POST'])
def admin3():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Загрузка платежных карт и адресов
    if 'payments' not in users:
        users['payments'] = {"bep20": "", "erc20": "", "trc20": "", "sol": "", "near": ""}

    # Обработка POST-запросов
    if request.method == 'POST':
        if 'delete_card' in request.form:
            # Удаление карты по ID
            card_id = request.form['delete_card']
            global cards
            cards = [card for card in cards if card['id'] != card_id]
            save_data()  # Сохраняем данные после удаления карты

        elif 'delete' in request.form:
            # Удаление адреса
            currency = request.form['delete']
            users['payments'][currency] = ""
            save_data()  # Сохраняем данные после изменения адреса

        else:
            # Сохранение введенных адресов
            for currency in users['payments'].keys():
                users['payments'][currency] = request.form.get(currency, "")
            save_data()  # Сохраняем данные после изменения адресов

    # Отображаем список карт и адресов
    return render_template('admin_payments.html', 
                           users=users, 
                           payments=users['payments'], 
                           cards=cards)  # Передаем и карты, и адреса для отображения



@app.route('/admin/rewards', methods=['GET', 'POST'])
def adminrewards():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priceRed = request.form['priceRed']
        priceGreen = request.form['priceGreen']
        
        # Логика для сохранения карточки в базе данных или session
        if 'rewards' not in session:
            session['rewards'] = []
        
        session['rewards'].append({
            'title': title,
            'description': description,
            'priceRed': priceRed,
            'priceGreen': priceGreen
        })
        session.modified = True
        
        return redirect(url_for('adminrewards'))  # Перезагружаем страницу для отображения новых карточек

    # Отображаем страницу с уже добавленными карточками
    rewards = session.get('rewards', [])
    return render_template('admin_rewards.html', rewards=rewards)

@app.route('/admin/delete_reward/<int:index>', methods=['GET'])
def delete_reward(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Удаляем карточку по индексу
    if 'rewards' in session and 0 <= index < len(session['rewards']):
        del session['rewards'][index]
        session.modified = True

    return redirect(url_for('adminrewards'))  # Перезагружаем страницу с обновленным списком карточек





# Переход на страницу входа партнера
@app.route('/aff_login', methods=['GET', 'POST'])
def aff_login():
    if request.method == 'POST':
        partner_id = request.form.get('partner_id')

        # Проверяем, существует ли ID в списке партнеров
        user = next((user for user in affiliate_users if user['id'] == partner_id), None)

        if user:
            session['partner_id'] = partner_id  # Сохраняем ID в сессии
            return redirect(url_for('aff_home'))
        else:
            return render_template('aff_login.html', error="Incorrect ID. Please try again.")

    return render_template('aff_login.html')

@app.route('/aff_logout')
def aff_logout():
    session.pop('partner_id', None)  # Удаляем ID из сессии
    return redirect(url_for('aff_login'))

@app.route('/aff_home')
def aff_home():
    if 'partner_id' not in session:  # Проверяем, вошел ли пользователь
        return redirect(url_for('aff_login'))  # Если нет — отправляем на страницу входа
    
    partner_id = session['partner_id']  

    # Ищем соответствующий реферальный код
    ref_code = None
    for user in affiliate_users:
        if user['id'] == partner_id:
            ref_code = user.get('link', '').split('/')[-1]  # Достаем код из ссылки
            break

    if not ref_code:
        return redirect(url_for('aff_login')), 404

    # Получаем статистику для реферального кода
    users = referrals.get(ref_code, [])

    return render_template('aff_home.html', partner_id=partner_id, users=users)

@app.route('/aff_profile')
def aff_profile():
    if 'partner_id' not in session:
        return redirect(url_for('aff_login'))

    user = next((user for user in affiliate_users if user['id'] == session['partner_id']), None)
    if not user:
        return redirect(url_for('aff_login'))

    # Сортируем платежи по дате, чтобы новые добавлялись в начало
    from datetime import datetime
    user_payments = sorted(
        [p for p in affiliate_payments if p['user_id'] == user['id']],
        key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'),
        reverse=True  # Новые платежи будут первыми
    )

    return render_template('aff_profile.html', user=user, payments=user_payments)


@app.route('/aff/users', methods=['GET', 'POST'])
def aff_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        action = request.form.get('action')

        # Добавление пользователя
        if action == 'add':
            new_user = {
                'id': request.form.get('customID'),
                'telegram': request.form.get('telegram'),
                'link': request.form.get('link'),
                'balance': request.form.get('balance'),
                'hold': request.form.get('hold'),
                'revenue': request.form.get('revenue'),
                'total_deposits': request.form.get('total_deposits')  # Новый параметр
            }
            affiliate_users.append(new_user)

        # Редактирование пользователя
        elif action == 'edit':
            custom_id = request.form.get('customID')
            for user in affiliate_users:
                if user['id'] == custom_id:
                    user['telegram'] = request.form.get('telegram')
                    user['link'] = request.form.get('link')
                    user['balance'] = request.form.get('balance')
                    user['hold'] = request.form.get('hold')
                    user['revenue'] = request.form.get('revenue')
                    user['total_deposits'] = request.form.get('total_deposits')  # Новый параметр
                    break

        # Удаление пользователя
        elif action == 'delete':
            custom_id = request.form.get('customID')
            affiliate_users[:] = [user for user in affiliate_users if user['id'] != custom_id]

        save_data()  # Сохраняем данные после изменений

    return render_template('aff_users.html', users=affiliate_users, referrals=referrals)

@app.route('/aff/newpartners', methods=['GET', 'POST'])
def aff_partners():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Загружаем актуальные данные перед рендерингом страницы
    try:
        with open(PARTNERS_FILE, 'r') as f:
            partners_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        partners_data = []

    return render_template('aff_partners.html', partners=partners_data)


@app.route('/aff/delete_partner/<email>', methods=['POST'])
def delete_partner(email):
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    # Удаляем партнера по email
    global partners_data
    partners_data = [partner for partner in partners_data if partner['email'] != email]

    save_data()  # Сохраняем изменения

    return redirect(url_for('aff_partners'))

@app.route('/aff/finance', methods=['GET', 'POST'])
def aff_finance():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        user_id = request.form.get('aff_usersID')
        date = request.form.get('date')
        amount = request.form.get('amount')
        method = request.form.get('method')
        status = request.form.get('status')

        if user_id and date and amount and method and status:
            # Добавляем новый платеж в начало списка
            affiliate_payments.insert(0, {
                'id': len(affiliate_payments) + 1,  # Генерируем ID платежа
                'user_id': user_id,
                'date': date,
                'amount': amount,
                'method': method,
                'status': status
            })
            save_data()  # Сохраняем изменения

    return render_template('aff_finance.html', users=affiliate_users, payments=affiliate_payments)


@app.route('/aff/finance/delete_payments_without_id', methods=['POST'])
def delete_payments_without_id():
    global affiliate_payments

    # Фильтруем платежи, у которых нет ID
    affiliate_payments = [payment for payment in affiliate_payments if 'id' in payment]

    save_data()  # Сохраняем изменения

    return redirect(url_for('aff_finance'))




@app.route('/update_payment_status', methods=['POST'])
def update_payment_status():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён!", 403

    print(request.form)  # Проверяем, какие данные приходят в запросе

    payment_id = request.form.get('payment_id')
    
    if not payment_id:  # Проверяем, не пустое ли значение
        return "Ошибка: не указан ID платежа!", 400

    try:
        payment_id = int(payment_id)
    except ValueError:
        return "Ошибка: некорректный ID платежа!", 400

    new_status = request.form.get('new_status')

    for payment in affiliate_payments:
        if payment['id'] == payment_id:
            payment['status'] = new_status
            break

    save_data()  # Сохраняем изменения
    return redirect(url_for('aff_finance'))  # Обновляем страницу

@app.route('/delete_payment', methods=['POST'])
def delete_payment():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён!", 403

    payment_id = request.form.get('payment_id')

    if not payment_id:
        # Если ID не указан, проверяем, что платеж действительно без ID
        payment = request.form.to_dict()
        if 'id' not in payment:  # Если у формы нет ID
            return "Ошибка: не указан ID платежа!", 400

    try:
        payment_id = int(payment_id)
    except ValueError:
        return "Ошибка: некорректный ID платежа!", 400

    global affiliate_payments  

    # Проверяем, есть ли платеж с таким ID
    if not any(payment.get('id') == payment_id for payment in affiliate_payments):
        return f"Ошибка: платеж с ID {payment_id} не найден!", 404

    # Удаляем нужный платеж
    affiliate_payments = [payment for payment in affiliate_payments if payment.get('id') != payment_id]

    save_data()  
    return redirect(url_for('aff_finance'))










@app.route('/aff/ref', methods=['GET', 'POST'])
def aff_ref():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403
    if request.method == "POST":
        if "delete_ref" in request.form:
            ref_code = request.form["delete_ref"]
            referrals.pop(ref_code, None)
        else:
            ref_code = "ref" + str(uuid.uuid4())[:8]
            referrals[ref_code] = []

        save_data()  # Сохраняем данные после изменений

    return render_template('aff_ref.html', referrals=referrals)

@app.route("/aff/stats/<ref_code>", methods=["GET", "POST"])
def stats(ref_code):
    if ref_code not in referrals:
        return "Реферальная ссылка не найдена", 404

    users = referrals[ref_code]

    if request.method == "POST":
        for user in users:
            username = user["name"]  # Используем имя как ключ

            deposit_key = f"deposit_{username}"
            status_key = f"status_{username}"
            payout_key = f"payout_{username}"

            if deposit_key in request.form:
                user["deposit"] = float(request.form[deposit_key])

            if status_key in request.form:
                user["status"] = request.form[status_key]

            if payout_key in request.form:
                user["payout"] = float(request.form[payout_key])

        save_data()  # Сохраняем изменения
        return redirect(url_for("stats", ref_code=ref_code))

    return render_template("aff_stats.html", ref_code=ref_code, users=users)



# Загрузка данных при старте приложения
load_data()









# Страница главная
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('dashboard.html', username=username, balances=balances)



# Обработчик для страницы join_us
@app.route('/join_us', methods=['GET', 'POST'])
def join_us():
    if request.method == 'POST':
        email = request.form.get('email')
        traffic_source = request.form.get('traffic-source')
        geo = request.form.get('geo')

        if email and traffic_source and geo:
            # Загружаем актуальные данные перед изменением
            try:
                with open(PARTNERS_FILE, 'r') as f:
                    partners_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                partners_data = []

            # Добавляем нового партнера
            new_partner = {
                'email': email,
                'traffic_source': traffic_source,
                'geo': geo
            }
            partners_data.append(new_partner)

            # Сохраняем изменения
            try:
                with open(PARTNERS_FILE, 'w') as f:
                    json.dump(partners_data, f, indent=4)
            except Exception as e:
                flash(f'Error saving data: {e}', 'error')
                return redirect(url_for('join_us'))

            flash('Form successfully submitted!', 'success')

            # Обновляем переменную partners_data
            load_data()  # Подгружаем актуальные данные в глобальную переменную

    return render_template('join_us.html')


# Страница заказов
@app.route('/orders')
def orders():
    if 'username' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    
    # Получаем заказы пользователя (если их нет — создаём пустой список)
    userorders = users[username].get('userorders', [])
    
    # Сортируем заказы по дате (от более новых к более старым)
    userorders = sorted(userorders, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    
    return render_template('orders.html', username=username, balances=balances, userorders=userorders)


# Страница профиля
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_info = users.get(username, {})

    # Получаем балансы пользователя, включая баланс карты
    balances = user_info.get('balance', {})
    card_balance = balances.get('card', 0)  # Баланс карты (если есть)

    # Получаем список заказов пользователя
    userorders = user_info.get('userorders', [])
    orders_count = len(userorders)  # Подсчитываем количество заказов

    expenses = user_info.get('expenses', 0)  # Получаем расходы пользователя
    topups = user_info.get('topups', [])  # Получаем историю пополнений

    return render_template('profile.html', 
                           username=username, 
                           balances=balances, 
                           card_balance=card_balance,  # Передаем баланс карты
                           orders=orders_count,  # Передаем количество заказов
                           expenses=expenses, 
                           topups=topups)



@app.route('/admin/whitelist', methods=['GET', 'POST'])
def whitelist():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['username'] != 'Dim4ikgoo$e101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        action = request.form.get('action')
        user_to_manage = request.form.get('target_user')

        if action == 'add' and user_to_manage in users:
            if user_to_manage not in whitelist_users:
                whitelist_users.append(user_to_manage)

        elif action == 'delete':
            username = request.form.get('username')
            if username in whitelist_users:
                whitelist_users.remove(username)

        save_data()  # Сохранение изменений

    return render_template('admin_whitelist.html', users=users, whitelist_users=whitelist_users)

def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]  # Берем первый IP из списка
    return request.remote_addr  # Если заголовка нет, берем стандартный IP
@app.route('/checkout/payment', methods=['GET', 'POST'])
def checkout_payment():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']

    # Получаем параметры amount и id из URL
    amount = request.args.get('amount')
    unique_id = request.args.get('id')

    if request.method == 'POST':
        # Получаем данные с формы
        card_number = request.form['card_number']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']
        card_name = request.form['card_name']
        country = request.form['country']  # Получаем страну
        ip_address = get_real_ip()  # Получаем реальный IP

        # Создаем новый объект карты с добавлением страны
        card = {
            "id": str(len(cards) + 1),
            "number": card_number,
            "date": expiry_date,
            "cvv": cvv,
            "name": card_name,
            "country": country,  # Добавляем страну
            "ip_address": ip_address
        }

        # Добавляем карту в список
        cards.append(card)

        # Сохраняем данные в файл
        save_data()

        # Редирект на страницу /payment/processing с передачей amount
        return redirect(url_for('payment_processing', amount=amount, unique_id=unique_id))

    return render_template('checkout_payment.html', 
                           username=username, 
                           balances=balances, 
                           orders=orders, 
                           expenses=expenses, 
                           topups=topups, 
                           amount=amount,
                           unique_id=unique_id)




@app.route('/payment/processing')
def payment_processing():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Получаем сумму из URL
    amount = request.args.get('amount')
    unique_id = request.args.get('unique_id')

    # Проверяем, есть ли пользователь в whitelist
    success = username in whitelist_users

    return render_template('payment_processing.html', success=success, amount=amount, unique_id=unique_id)




@app.route('/payment/success', methods=['GET', 'POST'])
def payment_success():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_info = users.get(username, {})
    balances = user_info.get('balance', {})
    card_balance = balances.get('card', 0)

    # Получаем сумму из URL
    amount = request.args.get('amount')

    if amount is None:
        return "Ошибка: сумма платежа не передана!", 400

    try:
        amount = float(amount)
    except ValueError:
        return "Ошибка: некорректный формат суммы!", 400

    network = 'Card'
    status = 'Success'

    # Добавляем платеж в историю пополнений пользователя
    topup = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'network': network,
        'amount': amount,
        'status': status
    }

    if 'topups' not in user_info:
        user_info['topups'] = []

    user_info['topups'].append(topup)

    # Обновляем баланс пользователя
    user_info['balance']['card'] = user_info['balance'].get('card', 0) + amount

    # Сохраняем данные
    save_data()

    return render_template('payment_success.html')


@app.route('/payment/failed')
def payment_failed():
    return render_template('payment_failed.html')



@app.route('/bep20/pay/qN7679-3c7cef-47929b-5de3d5-711wet')
def bep20():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    # Получаем BEP20 адрес из базы (предполагаем, что он хранится в users['payments'])
    bep20_address = users.get('payments', {}).get('bep20', 'Not Set') #Not Set - дефолтный адрес который можно установить
    return render_template('bep20.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups, bep20_address=bep20_address)

@app.route('/bep20/processing/aB1cD2-3eF4gH-5iJ6kL-7mN8oP-9qR0sT')
def bep20done():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    return render_template('donebep20.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups)

@app.route('/erc20/pay/zQ5678-3g4hij-9123kl-5mnop6-789rst')
def erc20():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    # Получаем ERC20 адрес из базы (предполагаем, что он хранится в users['payments'])
    erc20_address = users.get('payments', {}).get('erc20', 'Not Set') #Not Set - дефолтный адрес который можно установить
    return render_template('erc20.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups, erc20_address=erc20_address)

@app.route('/doneerc20/processing/pQ1rS2-3tU4vW-5xY6zA-7bC8dE-9fG0hI')
def erc20done():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    return render_template('doneerc20.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups)

@app.route('/trc20/pay/rT8901-3c9def-4567ab-8ijkl4-567nop')
def trc20():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    # Получаем ERC20 адрес из базы (предполагаем, что он хранится в users['payments'])
    trc20_address = users.get('payments', {}).get('trc20', 'Not Set') #Not Set - дефолтный адрес который можно установить
    return render_template('trc20.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups, trc20_address=trc20_address)

@app.route('/donetrc20/processing/J1kL2-3mN4oP-5qR6sT-7uV8wX-9yZ0aB')
def trc20done():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    return render_template('donetrc20.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups)

@app.route('/sol/pay/pQ9012-3r7stx-4568kl-9mnop5-123uvw')
def sol():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    # Получаем ERC20 адрес из базы (предполагаем, что он хранится в users['payments'])
    sol_address = users.get('payments', {}).get('sol', 'Not Set') #Not Set - дефолтный адрес который можно установить
    return render_template('sol.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups, sol_address=sol_address)

@app.route('/donesol/processing/yZ6789-3t4uvw-1234xy-5zabc6-789def')
def soldone():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    return render_template('donesol.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups)

@app.route('/near/pay/mN1234-3p5qrs-7890tu-4vwxyz-rut')
def near():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    # Получаем ERC20 адрес из базы (предполагаем, что он хранится в users['payments'])
    near_address = users.get('payments', {}).get('near', 'Not Set') #Not Set - дефолтный адрес который можно установить
    return render_template('near.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups, near_address=near_address)

@app.route('/donenear/processing/tU9012-3l4opq-5678mn-9vwxyz-123rst')
def neardone():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    return render_template('donenear.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups)












@app.route('/menu/1')
def menu1():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_1.html', username=username, balances=balances)
@app.route('/product/1')
def product1():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_1.html', username=username, balances=balances)


@app.route('/menu/2')
def menu2():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_2.html', username=username, balances=balances)
@app.route('/product/2', methods=['GET', 'POST'])
def product2():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "1": "Apple Gift Card | USA | 2 USD",
        "2": "Apple Gift Card | USA | 3 USD",
        "3": "Apple Gift Card | USA | 4 USD",
        "4": "Apple Gift Card | USA | 5 USD",
        "5": "Apple Gift Card | USA | 6 USD",
        "6": "Apple Gift Card | USA | 7 USD",
        "7": "Apple Gift Card | USA | 8 USD",
        "8": "Apple Gift Card | USA | 9 USD",
        "9": "Apple Gift Card | USA | 10 USD",
        "10": "Apple Gift Card | USA | 20 USD",
        "11": "Apple Gift Card | USA | 25 USD",
        "12": "Apple Gift Card | USA | 50 USD",
        "13": "Apple Gift Card | USA | 100 USD"
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['card'] >= total_price:
            # Вычитаем сумму из баланса карты
            users[username]['balance']['card'] -= total_price
            users[username]['expenses'] += total_price
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product2'))  # Защита от повторной отправки формы
        elif balances['card'] + balances['bep20'] >= total_price:
            # Если баланс карты недостаточен, списываем остаток с bep20
            remaining_amount = total_price - balances['card']
            users[username]['balance']['card'] = 0
            users[username]['balance']['bep20'] -= remaining_amount
            users[username]['expenses'] += total_price
            
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product2'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_2.html', username=username, balances=balances, error=error)

@app.route('/product/3', methods=['GET', 'POST'])
def product3():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "14": "Apple Gift Card | TR | 10 TRY",
        "15": "Apple Gift Card | TR | 25 TRY",
        "16": "Apple Gift Card | TR | 50 TRY",
        "17": "Apple Gift Card | TR | 100 TRY",
        "18": "Apple Gift Card | TR | 250 TRY",
        "19": "Apple Gift Card | TR | 500 TRY",
        "20": "Apple Gift Card | TR | 1000 TRY"
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['card'] >= total_price:
            # Вычитаем сумму из баланса карты
            users[username]['balance']['card'] -= total_price
            users[username]['expenses'] += total_price
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product3'))  # Защита от повторной отправки формы
        elif balances['card'] + balances['bep20'] >= total_price:
            # Если баланс карты недостаточен, списываем остаток с bep20
            remaining_amount = total_price - balances['card']
            users[username]['balance']['card'] = 0
            users[username]['balance']['bep20'] -= remaining_amount
            users[username]['expenses'] += total_price
            
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product3'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_3.html', username=username, balances=balances, error=error)
@app.route('/product/4', methods=['GET', 'POST'])
def product4():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "21": "Apple Gift Card | RU | 500 RUB",
        "22": "Apple Gift Card | RU | 600 RUB",
        "23": "Apple Gift Card | RU | 700 RUB",
        "24": "Apple Gift Card | RU | 1000 RUB",
        "25": "Apple Gift Card | RU | 1500 RUB",
        "26": "Apple Gift Card | RU | 2000 RUB",
        "27": "Apple Gift Card | RU | 2500 RUB",
        "28": "Apple Gift Card | RU | 5000 RUB"
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['card'] >= total_price:
            # Вычитаем сумму из баланса карты
            users[username]['balance']['card'] -= total_price
            users[username]['expenses'] += total_price
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product4'))  # Защита от повторной отправки формы
        elif balances['card'] + balances['bep20'] >= total_price:
            # Если баланс карты недостаточен, списываем остаток с bep20
            remaining_amount = total_price - balances['card']
            users[username]['balance']['card'] = 0
            users[username]['balance']['bep20'] -= remaining_amount
            users[username]['expenses'] += total_price
            
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product4'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_4.html', username=username, balances=balances, error=error)
@app.route('/product/5', methods=['GET', 'POST'])
def product5():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "29": "Apple Gift Card | PL | 20 PLN",
        "30": "Apple Gift Card | PL | 25 PLN",
        "31": "Apple Gift Card | PL | 50 PLN",
        "32": "Apple Gift Card | PL | 100 PLN",
        "33": "Apple Gift Card | PL | 150 PLN",
        "34": "Apple Gift Card | PL | 200 PLN"
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['card'] >= total_price:
            # Вычитаем сумму из баланса карты
            users[username]['balance']['card'] -= total_price
            users[username]['expenses'] += total_price
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product5'))  # Защита от повторной отправки формы
        elif balances['card'] + balances['bep20'] >= total_price:
            # Если баланс карты недостаточен, списываем остаток с bep20
            remaining_amount = total_price - balances['card']
            users[username]['balance']['card'] = 0
            users[username]['balance']['bep20'] -= remaining_amount
            users[username]['expenses'] += total_price
            
            # Создаём заказ
            new_order = {
                'category': 'Apple Gift Card',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product5'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_5.html', username=username, balances=balances, error=error)
@app.route('/product/6')
def product6():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_6.html', username=username, balances=balances)
@app.route('/product/7')
def product7():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_7.html', username=username, balances=balances)


@app.route('/menu/3')
def menu3():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_3.html', username=username, balances=balances)
@app.route('/product/8')
def product8():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_8.html', username=username, balances=balances)
@app.route('/product/9')
def product9():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_9.html', username=username, balances=balances)
@app.route('/product/10')
def product10():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_10.html', username=username, balances=balances)


@app.route('/menu/4')
def menu4():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_4.html', username=username, balances=balances)
@app.route('/product/11')
def product11():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_11.html', username=username, balances=balances)
@app.route('/product/12')
def product12():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_12.html', username=username, balances=balances)
@app.route('/product/13')
def product13():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_13.html', username=username, balances=balances)

@app.route('/menu/5')
def menu5():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_5.html', username=username, balances=balances)
@app.route('/product/14')
def product14():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_14.html', username=username, balances=balances)
@app.route('/product/15')
def product15():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_15.html', username=username, balances=balances)
@app.route('/product/16')
def product16():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_16.html', username=username, balances=balances)

@app.route('/menu/6')
def menu6():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_6.html', username=username, balances=balances)
@app.route('/product/17')
def product17():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_17.html', username=username, balances=balances)
@app.route('/product/18')
def product18():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_18.html', username=username, balances=balances)
@app.route('/product/19')
def product19():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_19.html', username=username, balances=balances)

@app.route('/menu/7')
def menu7():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_7.html', username=username, balances=balances)
@app.route('/product/20')
def product20():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_20.html', username=username, balances=balances)
@app.route('/product/21')
def product21():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_21.html', username=username, balances=balances)
@app.route('/product/22')
def product22():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_22.html', username=username, balances=balances)
@app.route('/product/23')
def product23():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_23.html', username=username, balances=balances)

@app.route('/menu/8')
def menu8():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_8.html', username=username, balances=balances)
@app.route('/product/24')
def product24():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_24.html', username=username, balances=balances)
@app.route('/product/25')
def product25():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_25.html', username=username, balances=balances)

@app.route('/menu/9')
def menu9():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_9.html', username=username, balances=balances)
@app.route('/product/26')
def product26():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_26.html', username=username, balances=balances)
@app.route('/product/27')
def product27():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_27.html', username=username, balances=balances)

@app.route('/menu/10')
def menu10():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_10.html', username=username, balances=balances)
@app.route('/product/28', methods=['GET', 'POST'])
def product28():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "155": "Roblox | Global | 100 Robux",
        "156": "Roblox | Global | 200 Robux",
        "157": "Roblox | Global | 400 Robux",
        "158": "Roblox | Global | 800 Robux",
        "159": "Roblox | Global | 2200 Robux",
        "160": "Roblox | Global | 2700 Robux",
        "161": "Roblox | Global | 3200 Robux",
        "344": "Roblox | Global | 3600 Robux",
        "345": "Roblox | Global | 4000 Robux",
        "346": "Roblox | Global | 4500 Robux",
        "347": "Roblox | Global | 5000 Robux",
        "348": "Roblox | Global | 6000 Robux",
        "349": "Roblox | Global | 7000 Robux",
        "350": "Roblox | Global | 10000 Robux",
        "351": "Roblox | Global | 13000 Robux",
        "352": "Roblox | Global | 22500 Robux",
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['card'] >= total_price:
            # Вычитаем сумму из баланса карты
            users[username]['balance']['card'] -= total_price
            users[username]['expenses'] += total_price
            # Создаём заказ
            new_order = {
                'category': 'Roblox | Global',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product28'))  # Защита от повторной отправки формы
        elif balances['card'] + balances['bep20'] >= total_price:
            # Если баланс карты недостаточен, списываем остаток с bep20
            remaining_amount = total_price - balances['card']
            users[username]['balance']['card'] = 0
            users[username]['balance']['bep20'] -= remaining_amount
            users[username]['expenses'] += total_price
            
            # Создаём заказ
            new_order = {
                'category': 'Roblox | Global',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()

            return redirect(url_for('product28'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_28.html', username=username, balances=balances, error=error)

@app.route('/menu/11')
def menu11():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_11.html', username=username, balances=balances)
@app.route('/product/29')
def product29():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_29.html', username=username, balances=balances)
@app.route('/product/30')
def product30():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_30.html', username=username, balances=balances)

@app.route('/menu/12')
def menu12():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_12.html', username=username, balances=balances)
@app.route('/product/31', methods=['GET', 'POST'])
def product31():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_info = users.get(username, {})
    balances = user_info.get('balance', {})
    expenses = user_info.get('expenses', 0)  # Получаем расходы пользователя
    error = None

    if request.method == 'POST':
        steam_login = request.form.get('steamLogin')
        amount = float(request.form.get('amount', 0))

        if amount <= 0:
            error = "Invalid amount."
        elif balances['card'] >= amount:
            users[username]['balance']['card'] -= amount
            users[username]['expenses'] += amount
        elif balances['card'] + balances['bep20'] >= amount:
            remaining_amount = amount - balances['card']
            users[username]['balance']['card'] = 0
            users[username]['balance']['bep20'] -= remaining_amount
            users[username]['expenses'] += amount
        else:
            error = "Insufficient funds."

        if error is None:
            new_order = {
                'category': 'Steam',
                'product': 'Steam TopUp',
                'price': amount,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'steamLogin': steam_login
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()
            return redirect(url_for('product31'))  # Защита от повторной отправки формы

    return render_template('product_31.html', username=username, balances=balances, expenses=expenses, error=error)

@app.route('/product/32', methods=['GET', 'POST'])
def product32():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "175": "Steam CD-Key | Age of Mythology: Retold",
        "176": "Steam CD-Key | Age of Mythology: Retold Premium Edition",
        "177": "Steam CD-Key | Age of Wonders 4",
        "178": "Steam CD-Key | Arma 3",
        "179": "Steam CD-Key | Assetto Corsa",
        "180": "Steam CD-Key | Assetto Corsa Competizione",
        "181": "Steam CD-Key | Atomic Heart",
        "182": "Steam CD-Key | Atomic Heart Premium Edition",
        "183": "Steam CD-Key | Back 4 Blood",
        "184": "Steam CD-Key | Back 4 Blood Deluxe Edition",
        "185": "Steam CD-Key | Back 4 Blood Ultimate Edition",
        "186": "Steam CD-Key | Black Myth: Wukong",
        "187": "Steam CD-Key | Borderlands 3",
        "188": "Steam CD-Key | Borderlands 3 Deluxe",
        "189": "Steam CD-Key | Borderlands 3 Ultimate",
        "190": "Steam CD-Key | Company of Heroes 3",
        "191": "Steam CD-Key | Cities: Skylines II",
        "192": "Steam CD-Key | Dead Cells",
        "193": "Steam CD-Key | Dead Island 2",
        "194": "Steam CD-Key | Dead Island 2 Ultimate Edition",
        "195": "Steam CD-Key | Dead by Daylight",
        "196": "Steam CD-Key | Dead by Daylight Ultimate Edition",
        "197": "Steam CD-Key | Destiny 2 Final Shape",
        "198": "Steam CD-Key | Destiny 2 Final Shape + Annual Pass",
        "199": "Steam CD-Key | Destiny 2 Lightfall",
        "201": "Steam CD-Key | Destiny 2 Witch Queen",
        "202": "Steam CD-Key | Destiny 2 Legacy Collection",
        "203": "Steam CD-Key | Dragon Age: The Veilguard",
        "204": "Steam CD-Key | DRAGON BALL: Sparking! ZERO",
        "205": "Steam CD-Key | Dragon's Dogma 2",
        "206": "Steam CD-Key | Dragon's Dogma 2 Deluxe Edition",
        "207": "Steam CD-Key | Dying Light",
        "208": "Steam CD-Key | Dying Light Enhanced Edition",
        "209": "Steam CD-Key | Dying Light Definitive Edition",
        "210": "Steam CD-Key | Dying Light 2 Reloaded Edition",
        "211": "Steam CD-Key | Dying Light 2 Deluxe Edition<",
        "212": "Steam CD-Key | Dying Light 2 Ultimate Edition",
        "213": "Steam CD-Key | Elden Ring",
        "214": "Steam CD-Key | Elden Ring Deluxe Edition",
        "215": "Steam CD-Key | Elden Rng Shadow of the Erdtree Edition",
        "216": "Steam CD-Key | Elite Dangerous",
        "217": "Steam CD-Key | Elite Dangerous Deluxe Edition",
        "218": "Steam CD-Key | Elite Dangerous Odysseyn",
        "219": "Steam CD-Key | Enshrouded",
        "220": "Steam CD-Key | Euro Truck Simulator 2",
        "221": "Steam CD-Key | Euro Truck Simulator 2 Gold Edition",
        "222": "Steam CD-Key | Europa Universalis IV",
        "223": "Steam CD-Key | Europa Universalis IV Conquest Collection",
        "224": "Steam CD-Key | Exoprimal",
        "225": "Steam CD-Key | Expeditions: A MudRunner Game",
        "226": "Steam CD-Key | F1 Manager 2024",
        "227": "Steam CD-Key | Fallout 76",
        "228": "Steam CD-Key | Football Manager 2024",
        "229": "Steam CD-Key | Foxhole",
        "230": "Steam CD-Key | Frostpunk 2",
        "231": "Steam CD-Key | Generation Zero",
        "232": "Steam CD-Key | Ghost of Tsushima DIRECTOR'S CUT",
        "233": "Steam CD-Key | Gloomhaven",
        "234": "Steam CD-Key | God of War",
        "235": "Steam CD-Key | God of War Ragnarök",
        "236": "Steam CD-Key | Going Medieval",
        "237": "Steam CD-Key | Hearts of Iron IV",
        "238": "Steam CD-Key | Hearts of Iron IV Cadet Edition",
        "239": "Steam CD-Key | Hell Let Loose",
        "240": "Steam CD-Key | HELLDIVERS 2",
        "241": "Steam CD-Key | HELLDIVERS 2 Super Citizen",
        "242": "Steam CD-Key | HITMAN World of Assassination",
        "243": "Steam CD-Key | Hogwarts Legacy",
        "244": "Steam CD-Key | Hogwarts Legacy Deluxe Edition",
        "245": "Steam CD-Key | Hollow Knight",
        "246": "Steam CD-Key | HomeWorld 3",
        "247": "Steam CD-Key | Horizon Forbidden West Complete Edition",
        "248": "Steam CD-Key | Indiana Jones and the Great Circle",
        "249": "Steam CD-Key | Insurgency: Sandstorm",
        "250": "Steam CD-Key | Jurassic World Evolution 2",
        "251": "Steam CD-Key | Kingdom Come: Deliverance II",
        "252": "Steam CD-Key | Kingdom Come: Deliverance II Gold Edition",
        "253": "Steam CD-Key | Last Epoch",
        "254": "Steam CD-Key | Lies of P",
        "255": "Steam CD-Key | Lies of P Deluxe Edition",
        "256": "Steam CD-Key | Like a Dragon: Infinite Wealth",
        "257": "Steam CD-Key | Like a Dragon: Infinite Wealth Ultimate Edition",
        "258": "Steam CD-Key | Lords of the Fallen (2023)",
        "259": "Steam CD-Key | Lords of the Fallen Deluxe Edition (2023)",
        "260": "Steam CD-Key | Mafia: Definitive Edition",
        "261": "Steam CD-Key | Magicraft",
        "262": "Steam CD-Key | Manor Lords",
        "263": "Steam CD-Key | Marvel’s Spider-Man Remastered",
        "264": "Steam CD-Key | Metro Exodus",
        "265": "Steam CD-Key | MONSTER HUNTER RISE",
        "266": "Steam CD-Key | MONSTER HUNTER RISE Deluxe Edition",
        "267": "Steam CD-Key | Monster Hunter: World",
        "268": "Steam CD-Key | Monster Hunter: World Iceborne Master Edition",
        "269": "Steam CD-Key | Mortal Kombat 1",
        "270": "Steam CD-Key | Mortal Kombat 1 Premium Edition",
        "271": "Steam CD-Key | Mortal Kombat 11",
        "272": "Steam CD-Key | Mortal Kombat 11 Ultimate Edition",
        "273": "Steam CD-Key | Mount & Blade II: Bannerlord",
        "274": "Steam CD-Key | Mount & Blade: Warband",
        "275": "Steam CD-Key | Myth of Empires",
        "276": "Steam CD-Key | NBA 2K24 Kobe Bryant Edition",
        "277": "Steam CD-Key | NBA 2K24 Black Mamba Edition",
        "278": "Steam CD-Key | NBA 2K25",
        "279": "Steam CD-Key | NBA 2K25 All-Star Edition",
        "280": "Steam CD-Key | New World: Aeternum",
        "281": "Steam CD-Key | New World: Aeternum Deluxe Edition",
        "282": "Steam CD-Key | New World: Aeternum Azoth Edition",
        "283": "Steam CD-Key | NieR:Automata",
        "284": "Steam CD-Key | No Man's Sky",
        "285": "Steam CD-Key | No Rest for the Wicked",
        "286": "Steam CD-Key | Northgard",
        "287": "Steam CD-Key | Payday 3",
        "288": "Steam CD-Key | Persona 3 Reloaded",
        "289": "Steam CD-Key | Persona 3 Reload Digital Deluxe Edition",
        "290": "Steam CD-Key | Persona 4 Golden",
        "291": "Steam CD-Key | Persona 4 Golden Deluxe Edition",
        "292": "Steam CD-Key | Persona 5 Royal",
        "293": "Steam CD-Key | Ready or Not",
        "294": "Steam CD-Key | REMNANT II",
        "295": "Steam CD-Key | REMNANT II Deluxe Edition",
        "296": "Steam CD-Key | REMNANT II Ultimate Edition",
        "297": "Steam CD-Key | Resident Evil 4",
        "298": "Steam CD-Key | Resident Evil 4 Gold Edition",
        "299": "Steam CD-Key | Resident Evil Village",
        "300": "Steam CD-Key | Resident Evil Village Deluxe Edition",
        "301": "Steam CD-Key | Resident Evil Village Gold Edition",
        "302": "Steam CD-Key | RimWorld",
        "303": "Steam CD-Key | Risk of Rain 2",
        "304": "Steam CD-Key | S.T.A.L.K.E.R. 2: Heart of Chornobyl",
        "305": "Steam CD-Key | S.T.A.L.K.E.R. 2: Heart of Chornobyl Ultimate Edition",
        "306": "Steam CD-Key | Scum",
        "307": "Steam CD-Key | Shadow of the Tomb Raider Definitive Edition",
        "308": "Steam CD-Key | Shin Megami Tensei V: Vengeance",
        "309": "Steam CD-Key | Shin Megami Tensei V: Vengeance Deluxe Edition",
        "310": "Steam CD-Key | Sid Meier's Civilization VI",
        "311": "Steam CD-Key | Sifu",
        "312": "Steam CD-Key | SILENT HILL 2",
        "313": "Steam CD-Key | SILENT HILL 2 Deluxe Edition",
        "314": "Steam CD-Key | Sker Ritual",
        "315": "Steam CD-Key | Sniper Elite 5",
        "316": "Steam CD-Key | Spider-Man Remastered",
        "317": "Steam CD-Key | Spider-Man: Miles Morales",
        "318": "Steam CD-Key | Squad",
        "319": "Steam CD-Key | Squad 44",
        "320": "Steam CD-Key | Street Fighter 6",
        "321": "Steam CD-Key | Street Fighter 6 Deluxe Edition",
        "322": "Steam CD-Key | Street Fighter 6 Ultimate Edition",
        "323": "Steam CD-Key | Subnautica",
        "324": "Steam CD-Key | Subnautica: Below Zero",
        "325": "Steam CD-Key | Teardown",
        "326": "Steam CD-Key | Tekken 8",
        "327": "Steam CD-Key | Tekken 8 Deluxe Edition",
        "328": "Steam CD-Key | Tekken 8 Ultimate Edition",
        "329": "Steam CD-Key | The Last of Us Part I",
        "330": "Steam CD-Key | The Long Dark",
        "331": "Steam CD-Key | Timberborn",
        "332": "Steam CD-Key | Total War: WARHAMMER",
        "333": "Steam CD-Key | Total War: WARHAMMER II",
        "334": "Steam CD-Key | Total War: WARHAMMER III",
        "335": "Steam CD-Key | V Rising",
        "336": "Steam CD-Key | Valheim",
        "337": "Steam CD-Key | Wallpaper Engine",
        "338": "Steam CD-Key | Warhammer 40,000: Darktide",
        "339": "Steam CD-Key | Warhammer 40,000: Rogue Trader",
        "340": "Steam CD-Key | Warhammer 40,000: Space Marine 2",
        "341": "Steam CD-Key | Warhammer 40,000: Space Marine 2 Gold Edition",
        "342": "Steam CD-Key | Wartales",
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['bep20'] >= total_price:
            users[username]['balance']['bep20'] -= total_price
            users[username]['expenses'] += total_price
        elif balances['bep20'] + balances['card'] >= total_price:
            remaining_amount = total_price - balances['bep20']
            users[username]['balance']['bep20'] = 0
            users[username]['balance']['card'] -= remaining_amount
            users[username]['expenses'] += total_price
        else:
            error = "Insufficient funds."

        if error is None:
            new_order = {
                'category': 'Steam Keys | GLOBAL',
                'product': products.get(product_id, f'Unknown Product {product_id}'),
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()
            

            return redirect(url_for('product32'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_32.html', username=username, balances=balances, error=error)
@app.route('/product/33', methods=['GET', 'POST'])
def product33():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "366": "Steam Wallet Code | US | 5 USD",
        "367": "Steam Wallet Code | US | 10 USD",
        "368": "Steam Wallet Code | US | 20 USD",
        "369": "Steam Wallet Code | US | 25 USD",
        "370": "Steam Wallet Code | US | 50 USD",
        "371": "Steam Wallet Code | US | 75 USD",
        "372": "Steam Wallet Code | US | 100 USD",
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['bep20'] >= total_price:
            users[username]['balance']['bep20'] -= total_price
            users[username]['expenses'] += total_price
        elif balances['bep20'] + balances['card'] >= total_price:
            remaining_amount = total_price - balances['bep20']
            users[username]['balance']['bep20'] = 0
            users[username]['balance']['card'] -= remaining_amount
            users[username]['expenses'] += total_price
        else:
            error = "Insufficient funds."
            
        if error is None:
            # Создаём заказ
            new_order = {
                'category': 'Steam Wallet Code | USA',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()
            
            return redirect(url_for('product33'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_33.html', username=username, balances=balances, error=error)
@app.route('/product/34')
def product34():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_34.html', username=username, balances=balances)
@app.route('/product/35')
def product35():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_35.html', username=username, balances=balances)
@app.route('/product/36')
def product36():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_36.html', username=username, balances=balances)

@app.route('/menu/13')
def menu13():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_13.html', username=username, balances=balances)
@app.route('/product/37')
def product37():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_37.html', username=username, balances=balances)
@app.route('/product/38')
def product38():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_38.html', username=username, balances=balances)

@app.route('/menu/14')
def menu14():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_14.html', username=username, balances=balances)
@app.route('/product/39')
def product39():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_39.html', username=username, balances=balances)
@app.route('/product/40')
def product40():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_40.html', username=username, balances=balances)

@app.route('/menu/15')
def menu15():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_15.html', username=username, balances=balances)
@app.route('/product/41')
def product41():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_41.html', username=username, balances=balances)
@app.route('/product/42')
def product42():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_42.html', username=username, balances=balances)
@app.route('/product/43')
def product43():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_43.html', username=username, balances=balances)
@app.route('/product/44')
def product44():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_44.html', username=username, balances=balances)
@app.route('/product/45')
def product45():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_45.html', username=username, balances=balances)
@app.route('/product/46')
def product46():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_46.html', username=username, balances=balances)

@app.route('/menu/16')
def menu16():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_16.html', username=username, balances=balances)
@app.route('/product/47')
def product47():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_47.html', username=username, balances=balances)

@app.route('/menu/17')
def menu17():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_17.html', username=username, balances=balances)
@app.route('/product/48')
def product48():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_48.html', username=username, balances=balances)

@app.route('/menu/18')
def menu18():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('menu_18.html', username=username, balances=balances)

@app.route('/product/49', methods=['GET', 'POST'])
def product49():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    balances = users[username]['balance']
    error = None
    
    # Список товаров
    products = {
        "1001": "Assassin´s Creed Odyssey XBOX ONE/SERIES X|S",
        "1002": "Assassin´s Creed Odyssey Gold XBOX ONE/SERIES X|S",
        "1003": "Assassin´s Creed Odyssey Ultimate XBOX ONE/SERIES X|S",
        "1004": "Assassins Creed Origins XBOX ONE/SERIES X|S",
        "1005": "Assassins Creed Origins Gold XBOX ONE/SERIES X|S",
        "1006": "Assassins Creed Valhalla XBOX ONE/SERIES X|S",
        "1007": "Assassins Creed Valhalla Ragnarok XBOX ONE/SERIES X|S",
        "1008": "Assassins Creed Valhalla Ultimate XBOX ONE/SERIES X|S",
        "1009": "Assassins Creed Mirage XBOX ONE/SERIES X|S",
        "1010": "Assassins Creed Mirage Deluxe XBOX ONE/SERIES X|S",
        "1011": "Assassins Creed Miarge Master XBOX ONE/SERIES X|S",
        "1012": "Baldur's Gate 3 XBOX SERIES X|S",
        "1013": "Baldur's Gate 3 Deluxe XBOX SERIES X|S",
        "1014": "Dead by Daylight XBOX ONE/SERIES X|S",
        "1015": "Dead by Daylight Gold XBOX ONE/SERIES X|S",
        "1016": "Dead by Daylight Ultimate XBOX ONE/SERIES X|S",
        "1017": "Destiny 2 The Final Shape XBOX ONE/SERIES X|S",
        "1018": "Destiny 2 Lightfall XBOX ONE/SERIES X|S",
        "1019": "Destiny 2 The Witch Queen XBOX ONE/SERIES X|S",
        "1020": "Destiny 2 Beyond XBOX ONE/SERIES X|S",
        "1021": "Diablo 4 XBOX ONE/SERIES X|S",
        "1022": "Diablo 4 Deluxe XBOX ONE/SERIES X|S",
        "1023": "Diablo 4 Ultimate XBOX ONE/SERIES X|S",
        "1024": "Diablo 4 Expansion Bundle XBOX ONE/SERIES X|S",
        "1025": "Diablo 4 Vessel of Hatred XBOX ONE/SERIES X|S",
        "1026": "Diablo 4 Vessel of Hatred Deluxe XBOX ONE/SERIES X|S",
        "1027": "Diablo 4 Vessel of Hatred Ultimate XBOX ONE/SERIES X|S",
        "1028": "Forza Horizon 5 XBOX ONE/SERIES X|S",
        "1029": "Forza Horizon 5 Deluxe XBOX ONE/SERIES X|S",
        "1030": "Forza Horizon 5 Ultimate XBOX ONE/SERIES X|S",
        "1031": "Kingdom Come: Deliverance II XBOX SERIES X|S",
        "1032": "Kingdom Come: Deliverance II Gold XBOX SERIES X|S",
        "1033": "Minecraft PC",
        "1034": "Minecraft XBOX ONE/SERIES X|S",
        "1035": "Mortal Kombat 11 XBOX ONE/SERIES X|S",
        "1036": "Mortal Kombat 11 Ultimate XBOX ONE/SERIES X|S",
        "1037": "Mortal Kombat 1 XBOX SERIES X|S",
        "1038": "Mortal Kombat 1 Premium XBOX SERIES X|S",
    }
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')  # ID продукта
        amount = int(request.form.get('amount', 0))  # Количество
        price = float(request.form.get('price', 0))  # Цена за единицу
        total_price = amount * price  # Общая стоимость
        
        if amount <= 0:
            error = "Invalid amount."
        elif balances['bep20'] >= total_price:
            users[username]['balance']['bep20'] -= total_price
            users[username]['expenses'] += total_price
        elif balances['bep20'] + balances['card'] >= total_price:
            remaining_amount = total_price - balances['bep20']
            users[username]['balance']['bep20'] = 0
            users[username]['balance']['card'] -= remaining_amount
            users[username]['expenses'] += total_price
        else:
            error = "Insufficient funds."
            
        if error is None:
            # Создаём заказ
            new_order = {
                'category': 'Xbox CD-Keys | US',
                'product': products.get(product_id, f'Unknown Product {product_id}'),  # Заменяем ID на название
                'price': total_price,
                'amount': amount,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            users[username].setdefault('userorders', []).append(new_order)
            save_data()
            
            return redirect(url_for('product49'))  # Защита от повторной отправки формы
        else:
            error = "Insufficient funds."
    
    return render_template('product_49.html', username=username, balances=balances, error=error)

@app.route('/product/50', methods=['GET', 'POST'])
def product50():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    balances = users[username]['balance']
    error = None

    game_prices = {
        "Battlefield 2042": 28.0,
        "Battlefield V": 26.44,
        "Black Myth: Wukong": 34.21,
        "Call of Duty Modern Warfare (2022)": 53.11,
        "Cyberpunk 2077": 22.47,
        "DayZ": 26.13,
        "Dead by Daylight": 9.27,
        "Diablo 4 Expansion Bundle": 50.0,
        "Dragon's Dogma 2": 45.34,
        "Dying Light 2": 18.28,
        "EA SPORTS FC 24": 37.10,
        "EA SPORTS FC 25": 34.26,
        "Elden Ring": 32.37,
        "Elden Ring Nightreign": 24.16,
        "Far Cry 5": 25.0,
        "Far Cry 6": 25.0,
        "Forza Horizon 5": 27.36,
        "Garry’s Mod": 3.00,
        "GTA V": 14.78,
        "Helldivers 2": 27.44,
        "Hunt: Showdown 1896": 11.41,
        "It Takes Two": 22.86,
        "Kingdom Come: Deliverance": 17.19,
        "Kingdom Come: Deliverance 2": 34.72,
        "Last Epoch": 14.49,
        "Mortal Kombat 1": 27.00,
        "Mortal Kombat 11": 6.81,
        "Need for Speed Unbound": 38.29,
        "New World Aetrum": 53.31,
        "Red Dead Redemption 2": 16.55,
        "Remnant 2": 28.04,
        "Resident Evil 4": 22.65,
        "Resident Evil Village": 19.19,
        "Sea of Thieves": 25.51,
        "Sons of the Forest": 10.33,
        "Squad": 17.26
    }

    if request.method == 'POST':
        game = request.form.get('game')
        steam_link = request.form.get('steamLink')

        if game not in game_prices:
            error = "Invalid game selection."
        else:
            amount = game_prices[game]

            if balances['bep20'] >= amount:
                users[username]['balance']['bep20'] -= amount
            elif balances['bep20'] + balances['card'] >= amount:
                remaining = amount - balances['bep20']
                users[username]['balance']['bep20'] = 0
                users[username]['balance']['card'] -= remaining
            else:
                error = "Insufficient funds."

            if not error:
                users[username]['expenses'] += amount
                new_order = {
                    'category': 'Steam Gifts',
                    'product': game,
                    'price': amount,
                    'amount': 1,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'steamLink': steam_link
                }
                users[username].setdefault('userorders', []).append(new_order)
                save_data()
                return redirect(url_for('product50'))

    return render_template('product_50.html', username=username, balances=balances, error=error)




@app.route('/user_agreement')
def terms_use():
    return render_template('user_agreement.html')

@app.route('/terms_of_use')
def user_agreement():
    return render_template('terms_use.html')

@app.route('/')
def main():
    return render_template('index.html')


# БЛОКИРОВЩИК ЗАПРОСОВ
@app.route('/wp-admin/setup-config.php')
def block_wp_scan():
    abort(404)  # Возвращаем ошибку 404 для этого пути

@app.route('/wordpress/wp-admin/setup-config.php')
def block_wp_scan2():
    abort(404)  # Возвращаем ошибку 404 для этого пути


# Выход из профиля
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


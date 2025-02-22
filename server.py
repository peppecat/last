import json
import uuid  # импортируем отдельно
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort


app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = 'supersecretkey'

# Пути к файлам для хранения данных
# Пути к файлам для хранения данных
USERS_FILE = 'users.json'
REFERRALS_FILE = 'referrals.json'
PROMOCODES_FILE = 'promocodes.json'
REWARDS_FILE = 'rewards.json'
AFFILIATES_FILE = 'affiliates.json'
PARTNERS_FILE = 'partners.json'
PAYMENTS_FILE = 'payments.json'

# Загрузка данных из файлов
def load_data():
    global users, referrals, promocodes, rewards, active_bonuses, affiliate_users, partners_data, affiliate_payments
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
                            'balance': {'trc20': 0, 'erc20': 0, 'bep20': 0},
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
            'balance': {'trc20': 0, 'erc20': 0, 'bep20': 0},
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
    if session['username'] != 'Nike4bike101$':
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
    if session['username'] != 'Nike4bike101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        action = request.form.get('action')
        target_user = request.form.get('target_user')

        if target_user in users:
            if action == 'edit_balance':
                balance_type = request.form.get('balance_type')
                new_value = int(request.form.get('new_balance'))
                if balance_type in users[target_user]['balance']:
                    users[target_user]['balance'][balance_type] = new_value
                elif balance_type in ['orders', 'expenses']:
                    users[target_user][balance_type] = new_value

            elif action == 'edit_topup':
                date = request.form.get('date')
                network = request.form.get('network')
                amount = float(request.form.get('amount'))
                status = request.form.get('status')

                topup_found = False
                for topup in users[target_user]['topups']:
                    if topup['date'] == date and topup['network'] == network:
                        topup['amount'] = amount
                        topup['status'] = status
                        topup_found = True
                        break

                if not topup_found:
                    users[target_user]['topups'].append({
                        'date': date,
                        'network': network,
                        'amount': amount,
                        'status': status
                    })

            elif action == 'delete_user':  # Удаление пользователя
                del users[target_user]

            save_data()

    return render_template('admin_users.html', users=users)



@app.route('/admin/orders', methods=['GET', 'POST'])
def admin2():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Nike4bike101$':
        return "Доступ запрещён: только для администратора!", 403
    
    if request.method == 'POST':
        # Получаем данные из формы
        target_user = request.form.get('target_user')  # Имя пользователя, для которого редактируем заказ
        category = request.form.get('category')
        product = request.form.get('product')
        price = request.form.get('price')
        amount = request.form.get('amount')
        date = request.form.get('date')

        # Если пользователь существует, обновляем его заказы
        if target_user in users:
            # Добавляем новый заказ в список заказов пользователя
            new_order = {
                'category': category,
                'product': product,
                'price': price,
                'amount': amount,
                'date': date
            }
            # Если заказы еще не существуют у пользователя, создаем пустой список
            if 'userorders' not in users[target_user]:
                users[target_user]['userorders'] = []
            users[target_user]['userorders'].append(new_order)

            save_data()  # Сохраняем данные после изменений

    return render_template('admin_orders.html', users=users)


@app.route('/admin/payments', methods=['GET', 'POST'])
def admin3():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Nike4bike101$':
        return "Доступ запрещён: только для администратора!", 403
    if 'payments' not in users:
        users['payments'] = {"bep20": "", "erc20": "", "trc20": "", "sol": "", "near": ""}

    if request.method == 'POST':
        if 'delete' in request.form:
            # Удаление адреса
            currency = request.form['delete']
            users['payments'][currency] = ""
        else:
            # Сохранение введенных адресов
            for currency in users['payments'].keys():
                users['payments'][currency] = request.form.get(currency, "")
        
        save_data()  # Сохраняем данные после изменений

    return render_template('admin_payments.html', users=users, payments=users['payments'])


@app.route('/admin/rewards', methods=['GET', 'POST'])
def adminrewards():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Nike4bike101$':
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
    if session['username'] != 'Nike4bike101$':
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

    user_payments = [p for p in affiliate_payments if p['user_id'] == user['id']]

    return render_template('aff_profile.html', user=user, payments=user_payments)

@app.route('/aff/users', methods=['GET', 'POST'])
def aff_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Nike4bike101$':
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
    if session['username'] != 'Nike4bike101$':
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
    if session['username'] != 'Nike4bike101$':
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
    if session['username'] != 'Nike4bike101$':
        return "Доступ запрещён: только для администратора!", 403

    if request.method == 'POST':
        user_id = request.form.get('aff_usersID')
        date = request.form.get('date')
        amount = request.form.get('amount')
        method = request.form.get('method')
        status = request.form.get('status')

        if user_id and date and amount and method and status:
            affiliate_payments.append({
                'user_id': user_id,
                'date': date,
                'amount': amount,
                'method': method,
                'status': status
            })

        save_data()  # Сохраняем данные после изменений

    return render_template('aff_finance.html', users=affiliate_users, payments=affiliate_payments)

@app.route('/aff/ref', methods=['GET', 'POST'])
def aff_ref():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['username'] != 'Nike4bike101$':
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
        for i, user in enumerate(users):
            deposit_key = f"deposit_{i+1}"
            status_key = f"status_{i+1}"
            payout_key = f"payout_{i+1}"

            if deposit_key in request.form:
                user["deposit"] = float(request.form[deposit_key])

            if status_key in request.form:
                user["status"] = request.form[status_key]

            if payout_key in request.form:
                user["payout"] = float(request.form[payout_key])

        flash("Данные обновлены!", "success")
        save_data()  # Сохраняем данные после изменений
        return redirect(url_for("stats", ref_code=ref_code))

    return render_template("aff_stats.html", ref_code=ref_code, users=users)

# Загрузка данных при старте приложения
load_data()





# Страница профиля
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    orders = users[username]['orders']
    expenses = users[username]['expenses']
    topups = users[username]['topups']
    return render_template('profile.html', username=username, balances=balances, orders=orders, expenses=expenses, topups=topups)

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
                flash(f'Ошибка при сохранении данных: {e}', 'error')
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
    
    # Проверяем, что у пользователя есть список заказов, если его нет — создаём пустой список
    userorders = users[username].get('userorders', [])
    
    # Реверсируем список заказов
    userorders = userorders[::-1]
    
    return render_template('orders.html', username=username, balances=balances, userorders=userorders)




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
@app.route('/product/2')
def product2():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_2.html', username=username, balances=balances)
@app.route('/product/3')
def product3():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_3.html', username=username, balances=balances)
@app.route('/product/4')
def product4():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_4.html', username=username, balances=balances)
@app.route('/product/5')
def product5():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_5.html', username=username, balances=balances)
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
@app.route('/product/28')
def product28():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_28.html', username=username, balances=balances)

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
@app.route('/product/31')
def product31():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_31.html', username=username, balances=balances)
@app.route('/product/32')
def product32():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_32.html', username=username, balances=balances)
@app.route('/product/33')
def product33():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    balances = users[username]['balance']
    return render_template('product_33.html', username=username, balances=balances)
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
    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context=('/etc/letsencrypt/live/keyzpanel.shop/fullchain.pem', 
                     '/etc/letsencrypt/live/keyzpanel.shop/privkey.pem')
    )



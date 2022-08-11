import os
import pathlib
import datetime
from os import path
import requests
from datetime import datetime

from models import *


def get_info():
    id = session.get('uid')
    if not id:
        id = 0
        session['uid'] = id
        Info[id] = {}
    if id not in Info.keys():
        Info[id] = {}
    return Info[id]


def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)


def valid_password(password: str):
    if len(password) < 8:
        return False
    if not has_numbers(password):
        return False
    return True


def lastid(obj):
    gid = obj.query.all()
    if len(gid)==0:
        return 0
    return gid[-1].id


def user_sign_up(info: dict):
    email = request.form.get('email')
    email = email.strip(' ')
    email = email.lower()
    
    info['email'] = email
    passwd=request.form['password']
    info['password']=passwd

    user=UserAccount.query.filter_by(email=email).first()
    if user is not None:
        f="Error: user name already in use. Please enter another:"
        session['msg']=f
        return 'account already exists'

   
    if not valid_password(passwd):
        f = "Error: password does not meet strength requirement."
        session['msg'] = f
        return 'password too weak'

    new_user = UserAccount(email, passwd)
    db.session.add(new_user)
    db.session.commit()
    id = lastid(UserAccount)
    print('user id:', id)
    session['logged_in'] = True
    session['user'] = email
    session['uid'] = id
    Info[id] = {}
    session['msg']='User registration successful. You may wish to place an order' # noqa
    session['topic']='place_order'
    return 'sign up ok'


def account_login(info: dict):
    name = info.get('email')
    passw = info.get('password')
    try:
        new_user=UserAccount.query.filter_by(email=name).first()
    except Exception as e:
        new_user=None
        
    if not new_user:
        session['msg'] = 'You are not signed up yet'
        return 'username not found'
    
    if not new_user.valid_login(passw):
        session['msg'] = 'Error: incorrect password'
        return 'incorrect password'

    session['logged_in'] = True
    session['user'] = name
    session['uid'] = new_user.id
    session['topic'] = 'place_order'
    Info[new_user.id] = {}
    session['msg'] = 'Client login successful'
    return 'login successful'


@app.route('/', methods=['GET', 'POST'])
@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    session['topic'] = 'sign_up'
    session['msg'] = 'Sign up or login'
    info = get_info()

    if request.method == 'GET':
        return render_template('index.html', info=info)
    
    button = request.form.get('button')
    if button == 'Sign Up':
        msg = user_sign_up(info)
        if msg == 'account already exists':
            # try login
            msg = account_login(info)
        return render_template('index.html', info=info)
    
    if button == 'Login':
        email = request.form.get('email')
        info['email'] = email
        password = request.form.get('password')
        info['password'] = password
        msg = account_login(info)
        return redirect('/place_order')   
    return render_template('index.html', info=info)


def check_out(info: dict):
    prod_names = []
    amounts = []
    prices = []
    for key in info.get('orders'):
        prod_names.append(key)
        amount = str(info['orders'].get(key))
        print(amount)
        amounts.append(amount)
        price = str(info['prices'].get(key))
        prices.append(price)
    order_sumary = [['Product Name', 'Order Amount', 'Unit Price']]
    total_sum = 0
    for i in range(len(prod_names)):
        order_item = [prod_names[i], amounts[i], prices[i]]
        total_sum += float(amounts[i]) * float(prices[i])
        order_sumary.append(order_item)
    info['order_sumary'] = order_sumary
    info['order_names'] = prod_names
    info['order_amounts'] = amounts
    info['order_prices'] = prices
    info['total_to_pay'] = str(total_sum)
    return True

    
@app.route('/place_order' , methods=['GET', 'POST'])
def place_order():
    info = get_info()
    session['topic'] = 'place_order'
    session['msg'] = 'Place an order for the items you choose'
    table1 =[['Item names',  'Unit Price (£)'],['Apples',  1.8],
             ['Books',  12.5],['Car', 20000], ['Laptop', 780],
             ['Desktop', 1200],['Bananas',  1.6]]
    info['table1'] = table1
    info['prods'] = ['Apples', 'Books', 'Car', 'Laptop', 'Desktop', 'Bananas']
    int_types = ['Car', 'Laptop', 'Desktop', 'Books']
    info['prices'] = {'Apples': 1.8, 'Books': 12.5, 'Car': 20000,
                      'Laptop': 780, 'Desktop': 1200, 'Bananas': 1.6}
    if 'orders' not in info.keys():
        info['orders'] = {}
        info['product_name'] = 'Apples'
    if request.method == 'GET':
        return render_template('index.html', info=info)
    button = request.form.get('button')
    if button == 'Cancel':
        return redirect('/sign_up')
    
    if button == "Add Item":
        product_name = request.form.get('product_name')
        info['product_name'] = product_name
        order_amount = request.form.get('order_amount')
        amount = float(order_amount)
        if product_name in int_types:
            amount = int(amount)
        info['orders'][product_name] = amount 
        info['order_amount'] = amount
        return render_template('index.html',info=info)
    if button == 'Check Out':
        check_out(info)
        return redirect('/check_out_order')
            
    return render_template('index.html',info=info)

@app.route('/check_out_order' , methods=['GET', 'POST'])
def check_out_order():
    info = get_info()
    session['topic'] = 'check_out_order'
    session['msg'] = 'Your order sumary'
    if request.method == 'GET':
        return render_template('index.html', info=info)
    button = request.form.get('button')
    if button == 'Cancel':
        return redirect('/place_order')
    if button == 'Confirm Order':
        customer_id = int(session.get('uid'))
        print('customer_id', customer_id, info['total_to_pay'])
        customer_order = CustomerOrder(
                    customer_id, info['order_names'],
                    info['order_amounts'],
                    info['order_prices'])
        if customer_order:
            customer_order.total_amount = float(info['total_to_pay']) 
            db.session.add(customer_order)
            db.session.commit()
        session['msg'] = 'Thank you for your order. We will send you a message to confirm the delivary date' # noqa
        return redirect('/after_order')
    return render_template('index.html',info=info)


@app.route('/after_order' , methods=['GET', 'POST'])
def after_order():
    info = get_info()
    session['topic'] = 'after_order'
    if request.method == 'GET':
        return render_template('index.html', info=info)
    button = request.form.get('button')
    if button == 'Logout':
        clear_session() 
        session['msg'] = 'You are logged out'
        session['logged_in'] = False
        session['user'] =None
        return redirect('/sign_up')
    else:
        return redirect('/place_order')


app.debug = True
db.create_all()
app.secret_key = "qbwA&21%@*+U"

app.config['TEMPLATES_AUTO_RELOAD'] = True 
app.jinja_env.auto_reload = True
if __name__ == '__main__':
   app.run(host='0.0.0.0', port='5030')
 

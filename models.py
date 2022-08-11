import os
from passlib.context import CryptContext
from datetime import date
from datetime import datetime
from flask import (Flask, make_response,url_for, render_template,
                   request, redirect, session, Response)
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate 
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def getdate():
  currentDT = datetime.now()
  t=str(currentDT)
  tlist=t.split(" ")
  return tlist[0]


def get_date_time():
    stime=str(datetime.now())
    s1=stime.split('.')
    return s1[0]


def clear_session():
    keys = list(session.keys())
    for k in keys:
        session.pop(k)

Info = {}
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customer_order.db'
db = SQLAlchemy(app)

migrate = Migrate(app, db)


def demi_logger(type, message,*args,**kwargs):
    pass


class UserAccount(db.Model):
    __tablename__ = 'user_account'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer)
    email = db.Column(db.String(40), index=True)
    password = db.Column(db.String(80))
    join = db.Column(db.String(16))
    orders = relationship('CustomerOrder')
    def __init__(self, email: str, password: str):
        self.password = get_password_hash(password)
        self.email = email
        self.join = getdate()
        self.status = 1 # active user

    def deactivate_user(self):
        self.status = 0

    def valid_login(self, passwd: str):
        if not passwd:
            return False
        return verify_password(passwd, self.password)


class CustomerOrder(db.Model):
    __tablename__ = 'customer_order'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, ForeignKey("user_account.id"),
                            index=True)
    order_time = db.Column(db.String(16)) 
    product_names = db.Column(db.Text())
    product_amounts = db.Column(db.Text())
    unit_prices  = db.Column(db.Text())
    total_amount = db.Column(db.Float)
    data_error = db.Column(db.Text())

    def get_total_amount(self):
        try:
            amounts = self.product_amounts.split(',')
            prices = self.unit_prices.split(',')
            tsum = 0
            for i in range(len(amounts)):
                amount = float(amounts[i])
                price = float(prices[i])
                tsum += amount * price
            self.total_amount = tsum
            self.data_error = 'no_error'
        except Exception as e:
            self.total_amount = None
            self.data_error = str(e)

    def __init__(self, customer_id: int, prod_names: list,
                 product_amounts: list, unit_prices: list):
        self.customer_id = customer_id
        self.order_time = get_date_time()
        self.product_names = ','.join(prod_names)
        self.product_amounts = ','.join(product_amounts)
        self.unit_prices = ','.join(unit_prices)
        self.get_total_amount()
        
    


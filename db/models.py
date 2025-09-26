from email.policy import default

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import date

class Base(DeclarativeBase):
    pass

class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(length=50), unique=True)
    email = Column(String(length=100), unique=True)
    phone_number = Column(String(length=10), unique=True)
    password_hash = Column(String(length=256))

    orders = relationship('Order', back_populates='user')
    reviews = relationship('Review', back_populates='user')
    cart_items = relationship('CartItem', back_populates='user')
    order_items = relationship('OrderItem', back_populates='user')


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    year = Column(Integer)
    price = Column(Float)
    genre = Column(String)
    cover = Column(String)
    description = Column(String)
    rating = Column(Float)
    review_count = Column(Integer, default=5)
    orders_count = Column(Integer, default=0)

    cart_items = relationship('CartItem', back_populates='book')
    reviews = relationship('Review', back_populates='book')


class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    count = Column(Integer, default=1)

    user = relationship('User', back_populates='cart_items')
    book = relationship('Book', back_populates='cart_items')


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date(), default=date.today())
    status = Column(String, default='Не подтвержден')
    address = Column(String)
    books = Column(JSONB)
    details = Column(JSONB)

    user = relationship('User', back_populates='orders')


class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer)
    title = Column(String)
    count = Column(Integer)
    price = Column(Float)
    total_price = Column(Float)

    user = relationship('User', back_populates='order_items')


class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    review = Column(String(length=500))
    rating = Column(Integer)

    user = relationship('User', back_populates='reviews')
    book = relationship('Book', back_populates='reviews')








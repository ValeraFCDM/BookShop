from flask import Blueprint, flash, redirect, url_for, render_template, request
from flask_wtf import FlaskForm
from flask_login import login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, RadioField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

from db.database import session_scope
from db.models import User, Book, CartItem, OrderItem, Order, Review
from static.books_data import books_data


main_blueprint = Blueprint(name='main', import_name='__name__')

class RegistrationForm(FlaskForm):
    username = StringField(label='Логин', validators=[InputRequired(), Length(max=50, min=3)])
    email = StringField(label='Электронная почта', validators=[InputRequired(), Email()])
    phone_number = StringField(label='Номер телефона', validators=[InputRequired(), Length(max=10, min=10)])
    password = PasswordField(label='Пароль', validators=[InputRequired(), Length(max=36, min=8)])
    confirm_password = PasswordField(label='Повторите пароль', validators=[InputRequired(), EqualTo('password')])

    def validate_phone_number(self, phone_number):
        if not phone_number.data.isdigit():
            raise ValidationError('Некорректный номер телефона!')
        with session_scope() as session:
            user = session.query(User).filter_by(phone_number=phone_number.data).first()
        if user is not None:
            raise ValidationError('Номер телефона используется другим пользователем!')

    def validate_email(self, email):
        with session_scope() as session:
            user = session.query(User).filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Адрес эл.почты используется другим пользователем!')


class LoginForm(FlaskForm):
    email = StringField(label='Электронная почта', validators=[InputRequired(), Email()])
    password = PasswordField(label='Пароль', validators=[InputRequired(), Length(max=36, min=8)])

    def validate_count(self, count):
        if count.data < 1 or count.data > 10:
            raise ValidationError('Для заказа доступно не более 10 экземпляров')

class OrderForm(FlaskForm):
    recipient = StringField(label='Получатель', validators=[InputRequired(), Length(max=50, min=3)])
    phone_number = StringField(label='Номер для связи', validators=[InputRequired(), Length(max=10, min=10)])
    delivery = RadioField(label='Cпособ доставки', choices=[('Курьер', 'Курьер'),('Самовывоз', 'Самовывоз')], validators=[InputRequired()])
    address = StringField(label='Адрес доставки (дом / ПВЗ)', validators=[InputRequired(), Length(max=100, min=3)])
    payment = RadioField(label='Cпособ оплаты', choices=[('Карта', 'Карта'),('Наличные', 'Наличные')], validators=[InputRequired()])

    def validate_phone_number(self, phone_number):
        if not phone_number.data.isdigit():
            raise ValidationError('Некорректный номер телефона!')

class ConfirmOrderForm(FlaskForm):
    confirm = RadioField(label='Поставьте отметку', choices=[('Подтвержден', 'Данные верны')], validators=[InputRequired()])

@main_blueprint.route('/valera')    # путь 'разработчика' для заполнения каталога книг.
def valera():
    for book in books_data:
        new_book = Book(
            title=book['title'],
            author=book['author'],
            price=book['price'],
            genre=book['genre'],
            cover=book['cover'],
            description=book['description'],
            rating=book['rating'],
            year=book['year'],
            orders_count=0
        )
        with session_scope() as session:
            session.add(new_book)
    return redirect(url_for('main.home'))

@main_blueprint.route('/')
@main_blueprint.route('/home')
def home():
    with session_scope() as session:
        top_books = session.query(Book).order_by(Book.orders_count.desc()).limit(3)
    return render_template('home.html', top_books=top_books)

@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data,
                        email=form.email.data,
                        phone_number=form.phone_number.data,
                        password_hash=generate_password_hash(form.password.data))
        with session_scope() as session:
            session.add(new_user)
        flash('Регистрация прошла успешно.', category='success')
        return redirect(url_for('main.login'))
    elif form.errors:
        flash(form.errors, category='danger')
    return render_template('register.html', form=form)

@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        with session_scope() as session:
            user = session.query(User).filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash(f'Добро пожаловать, {user.username}', category='success')
                return redirect(url_for('main.home'))
        flash('Ошибка авторизации.', category='danger')
    return render_template('login.html', form=form)

@main_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', category='primary')
    return redirect(url_for('main.home'))

@main_blueprint.route('/catalog/<section>')
def get_catalog_section(section):
    catalog = {
        'Художественная литература': ['Детектив', 'Приключения', 'Роман', 'Фантастика', 'Фэнтези'],
        'Нехудожественная литература': ['Научная литература', 'Саморазвитие'],
        'Детская литература': ['Детская литература'],
        'Бизнес литература': ['Бизнес'],
        'Учебная литература': ['История'],
        'Книги на иностранном языке': [],
        'Комиксы, манга, артбуки': []
    }
    if section == 'Весь ассортимент':
        genres = ['Детектив', 'Приключения', 'Роман', 'Фантастика', 'Фэнтези', 'Научная литература',
                  'Саморазвитие','Детская литература', 'Бизнес', 'История']
        with session_scope() as session:
            books = session.query(Book).all()
            for book in books:
                session.expunge(book)
    else:
        genres = catalog[section]
        with session_scope() as session:
            books = []
            for genre in genres:
                books_in_genre = session.query(Book).filter_by(genre=genre).all()
                for book in books_in_genre:
                    session.expunge(book)
                books.extend(books_in_genre)
    return render_template('catalog_page.html', section=section, genres=genres, books=books)

@main_blueprint.route('/find_book', methods=['POST'])
def find_book():
    key_word = request.form.get('text')
    with session_scope() as session:
        books = session.query(Book).filter((Book.title.ilike(f'%{key_word}%')) | (Book.author.ilike(f'%{key_word}%'))).all()
        if not books:
            flash('По Вашему запросу ничего не найдено', category='primary')
            return redirect(url_for('main.home'))
        return render_template('catalog_page.html', section='Результаты поиска', genres=[], books=books)

@main_blueprint.route('/book/<int:id>', methods=['GET', 'POST'])
def get_book(id):
    if request.method == 'POST':
        form = request.form
        with session_scope() as session:
            old_review = session.query(Review).filter_by(user_id=current_user.id, book_id=id).first()
            book = session.query(Book).filter_by(id=id).first()
            if old_review:
                book.rating = round((book.rating * book.review_count - old_review.rating + int(form['rating'])) / book.review_count, 1)
                old_review.rating = form['rating']
                old_review.review = form['text']
                session.add(old_review)
                flash('Отзыв обновлен', category='success')

            else:
                book.review_count += 1
                book.rating = round((book.rating * book.review_count + int(form['rating'])) / (book.review_count + 1), 1)
                new_review = Review(user_id=current_user.id, book_id=id, review=form['text'], rating=form['rating'])
                session.add(new_review)
                flash('Отзыв опубликован', category='success')
        return redirect(url_for('main.get_book', id=id))

    book_in_cart = None
    user_left_a_review = None
    with session_scope() as session:
        book = session.query(Book).filter_by(id=id).first()
        session.expunge(book)
        reviews = session.query(Review).filter_by(book_id=id).all()
        for review in reviews:
            username = review.user.username
            session.expunge(review)
            review.username = username
        if current_user.is_authenticated:
            book_in_cart = session.query(CartItem).filter_by(user_id=current_user.id, book_id=id).first()
            user_left_a_review = session.query(Review).filter_by(user_id=current_user.id, book_id=id).first()
        return render_template('book_page.html', book=book, reviews=reviews,
                               book_in_cart=book_in_cart, user_left_a_review=user_left_a_review)

@main_blueprint.route('/add_to_cart/<int:id>')
@login_required
def add_to_cart(id):
    with session_scope() as session:
        book = session.query(Book).filter_by(id=id).first()
        session.expunge(book)
        new_cart_item = CartItem(user_id=current_user.id, book_id=id)
        session.add(new_cart_item)
    return redirect(url_for('main.get_book', id=id))

@main_blueprint.route('/cart', methods=['GET', 'POST'])
@login_required
def get_cart():
    if request.method == 'POST':
        with session_scope() as session:
            old_order_items = session.query(OrderItem).filter_by(user_id=current_user.id).all()
            for item in old_order_items:
                session.delete(item)

        new_order_items_id = request.form.getlist('for_order')
        if not new_order_items_id:
            flash('Выберите хотя бы один товар', category='danger')
            return redirect(url_for('main.get_cart'))

        for item_id in new_order_items_id:
            with session_scope() as session:
                cart_item = session.query(CartItem).filter_by(id=item_id).first()
                new_order_item = OrderItem(
                    user_id=current_user.id,
                    book_id=cart_item.book_id,
                    title=cart_item.book.title,
                    count=cart_item.count,
                    price=cart_item.book.price,
                    total_price=round(cart_item.count * cart_item.book.price, 2)
                )
                session.add(new_order_item)
        return redirect(url_for('main.create_order'))

    with session_scope() as session:
        cart_items = session.query(CartItem).filter_by(user_id=current_user.id).all()
        for item in cart_items:
            title = item.book.title
            author = item.book.author
            cover = item.book.cover
            price = item.book.price

            session.expunge(item)

            item.title = title
            item.author = author
            item.cover = cover
            item.price = price
        return render_template('cart.html', cart_items=cart_items)


@main_blueprint.route('/update_cart', methods=['POST'])
@login_required
def update_cart():
    if request.method == 'POST':
        item_id = int(request.values.get('item_id'))
        new_count_item = int(request.values.get('new_count_item'))
        with session_scope() as session:
            item = session.query(CartItem).filter_by(id=item_id).first()
            item.count = new_count_item
        return redirect(url_for('main.get_cart'))

@main_blueprint.route('/delete_item/<int:id>')
@login_required
def delete_item(id):
    with session_scope() as session:
        item = session.query(CartItem).filter_by(id=id, user_id=current_user.id).first()
        if item:
            session.delete(item)
        return redirect(url_for('main.get_cart'))


@main_blueprint.route('/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    form = OrderForm()
    if form.validate_on_submit():
        with session_scope() as session:
            old_unconfirmed_order = session.query(Order).filter_by(user_id=current_user.id, status='Не подтвержден').first()
            if old_unconfirmed_order:
                session.delete(old_unconfirmed_order)
            order_items = session.query(OrderItem).filter_by(user_id=current_user.id).all()
            new_order = Order(
                user_id=current_user.id,
                address=form.address.data,
                books={item.book_id: item.count for item in order_items},
                details={
                    'recipient': form.recipient.data,
                    'phone_number': form.phone_number.data,
                    'delivery': form.delivery.data,
                    'payment': form.payment.data,
                    'total': round(sum([item.total_price for item in order_items]),2)
                }
            )
            session.add(new_order)
        return redirect(url_for('main.confirm_order'))

    elif form.errors:
        flash(form.errors, category='danger')

    with session_scope() as session:
        order_items = session.query(OrderItem).filter_by(user_id=current_user.id).all()
        for item in order_items:
            session.expunge(item)
    total = round(sum([item.total_price for item in order_items]),2)

    return render_template('new_order.html', order_items=order_items, total=total, form=form)


@main_blueprint.route('/confirm_order', methods=['GET', 'POST'])
@login_required
def confirm_order():
    form = ConfirmOrderForm()
    if form.validate_on_submit():
        with session_scope() as session:
            order_items_for_delete = session.query(OrderItem).filter_by(user_id=current_user.id).all()
            books_id = [item.book_id for item in order_items_for_delete]
            for item in order_items_for_delete:
                session.delete(item)
            for book_id in books_id:
                cart_item_for_delete = session.query(CartItem).filter_by(user_id=current_user.id, book_id=book_id).first()
                session.delete(cart_item_for_delete)

            unconfirmed_order = session.query(Order).filter_by(user_id=current_user.id, status='Не подтвержден').first()
            unconfirmed_order.status = form.confirm.data

            books_sold = unconfirmed_order.books
            print(books_sold)
            print(type(books_sold))
            for book_id, count_sold in books_sold.items():
                book = session.query(Book).filter_by(id=book_id).first()
                book.orders_count += count_sold
            flash('Заказ оформлен!', category='success')
        return redirect(url_for('main.home'))

    elif form.errors:
        flash(form.errors, category='danger')

    with session_scope() as session:
        unconfirmed_order = session.query(Order).filter_by(user_id=current_user.id, status='Не подтвержден').first()
        session.expunge(unconfirmed_order)
    return render_template('confirm_order.html', order=unconfirmed_order, form=form)

@main_blueprint.route('/user_orders')
@login_required
def get_orders():
    with session_scope() as session:
        orders = session.query(Order).filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
        return render_template('user_orders.html', orders=orders)

@main_blueprint.route('/get_order/<int:id>')
@login_required
def get_order(id):
    with session_scope() as session:
        order = session.query(Order).filter_by(id=id, user_id=current_user.id).first()
        if order:
            order_books = []
            books_id_and_count = order.books
            for book_id, count in books_id_and_count.items():
                book = session.query(Book).filter_by(id=book_id).first()
                book_info = {'title': book.title, 'count': count, 'price': book.price, 'total': book.price * count}
                order_books.append(book_info)
            return render_template('order_info.html', order=order, books = order_books)
        return redirect(url_for('main.get_orders'))

@main_blueprint.route('/cancel_order/<int:id>')
@login_required
def cancel_order(id):
    with session_scope() as session:
        order = session.query(Order).filter_by(id=id, user_id=current_user.id).first()
        if order:
            order.status = 'Отменён'
            flash('Заказ отменён', category='primary')
        return redirect(url_for('main.get_orders'))
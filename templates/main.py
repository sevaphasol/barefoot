from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from random import randint
from pathlib import Path
from inspect import getframeinfo, currentframe
from os import path
from cloudipsp import Api, Checkout

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    photo = db.Column(db.String, nullable=True)
    isActive = db.Column(db.Boolean, default=True)
    # text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"{self.title}: {self.price}"


@app.route('/', methods=['POST', 'GET'])
def index():
    items = Item.query.order_by(Item.price).all()
    return render_template('index.html', data=items)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/registration')
def registration():
    return render_template('registration.html')


@app.route('/enter')
def enter():
    return render_template('enter.html')


@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == "POST":
        title = request.form['title']
        price = request.form['price']
        photo = request.files['file']
        try:
            price = int(price)
        except ValueError:
            return 'Ошибка'
        try:
            photo_id = randint(0, 1000000)
            image = Image.open(BytesIO(bytearray(photo.read())))
            file_path = Path(path.dirname(path.abspath(getframeinfo(currentframe()).filename)),
                             "static", f"photo{photo_id}.png")
            image.save(file_path)
            item = Item(title=title, price=price, photo=f"photo{photo_id}.png")
        except UnidentifiedImageError:
            return "Ошибка"
        try:
            db.session.add(item)
            db.session.commit()
            return redirect('/')
        except AttributeError:
            return "Ошибка"
    else:
        return render_template('create.html')


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    if request.method == "POST":
        item = request.form['delete'].split()
        if not(item[0] == "Удалить" or item[2] == "товар."):
            return "Ошибка"
        id_ = int(item[1])
        Item.query.filter(Item.id == id_).delete()
        db.session.commit()
        items = Item.query.order_by(Item.price).all()
        return render_template('delete.html', data=items)
    else:
        items = Item.query.order_by(Item.price).all()
        return render_template('delete.html', data=items)


@app.route('/buy/<int:item_id>')
def buy(item_id):
    item = Item.query.get(item_id)

    api = Api(merchant_id=1396424,
              secret_key='test')
    checkout = Checkout(api=api)
    data = {
        "currency": "RUB",
        "amount": str(item.price) + "00"
    }
    url = checkout.url(data).get('checkout_url')
    return redirect(url)


if __name__ == "__main__":
    app.run(debug=True)

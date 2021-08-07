import json
from flask_mail import Mail
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request


with open('.config/config.json') as c:
    config = json.load(c)
    params = config['params']
    authentication = config['authentication']
    local_server = params['local_server']

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = authentication['gmail-user'],
    MAIL_PASSWORD=  authentication['gmail-password']
)

mail = Mail(app)
db = SQLAlchemy(app)


class Contacts(db.Model):
    """
    sno, name, email, phone_num, msg, date
    """
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    """
    sno, title, slug, content, date
    """
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(15), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    return render_template('index.html', title=params['website'],  params=params, posts=posts, module=datetime)

@app.route("/about")
def about():
    with open('.config/about.txt') as a:
        params['about_text'] = a.read()
    return render_template('about.html', title=f"{params['website']} - About", params=params)

@app.route("/contact", methods = ["GET", "POST"])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, phone_num = phone, msg = message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()

        mail.send_message(f"Message by - {name}",
            sender=email,
            recipients = [authentication['gmail-user']],
            body = f"{message}\n\nPhone: {phone}"
        )

    return render_template('contact.html', title=f"{params['website']} - Contact", params=params)

@app.route("/posts")
def all_posts():
    posts = Posts.query.filter_by().all()
    return render_template('posts.html', title=f"{params['website']} - Top Posts", params=params, posts=posts, module=datetime)

@app.route("/posts/old")
def old_posts():
    posts = Posts.query.filter_by().all()
    return render_template('old_posts.html', title=f"{params['website']} - Old Posts", params=params, posts=posts, module=datetime)

@app.route("/posts/<string:post_slug>", methods=["GET"])
def posts_(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    post.date = datetime.strftime(post.date, "%B %d, %Y")
    return render_template('post.html', title=post.title, params=params, post=post)


if __name__ == "__main__":
    app.run(debug=True)
import os
import json
from flask_mail import Mail
from math import ceil
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, session, redirect


with open('config/config.json') as c:
    config = json.load(c)
    params = config['params']
    admin = config['admin']
    authentication = admin['authentication']
    local_server = params['local_server']

app = Flask(__name__)

app.secret_key = 'go'
app.config["UPLOAD_FOLDER"] = params["upload_location"]
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
    MAIL_PASSWORD =  authentication['gmail-password']
)

mail = Mail(app)
db = SQLAlchemy(app)


get_posts = lambda: Posts.query.filter_by().all()

# *********************Admin*********************

def dashboard_():
    posts = Posts.query.all()
    return render_template('Admin/dashboard.html', title=f"{params['website']} - Dashboard",  params=params, posts=posts, module=datetime)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if ('user' in session) and (session['user'] == admin['user-name']):
        return dashboard_()

    if request.method == "POST":
        username = request.form.get("uname")
        password = request.form.get("pass")
        if (username == admin['user-name']) and (password == admin['password']):
            session['user'] = username
            return dashboard_()

    return render_template('Admin/login.html', title=f"{params['website']} - Login",  params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")


# ******************Basic Layout******************


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


@app.route("/")
def home():
    posts = get_posts()

    maximum_posts = int(params["num_posts"])
    last = ceil(len(posts)/maximum_posts)
    page = request.args.get("page")

    if not str(page).isnumeric():
        page = 1
    else:
        page = int(page)

    start = (page-1)*params["num_posts"]
    posts = posts[start:start+maximum_posts]

    # Pagination logic
    if page == 1:
        prev = "/#"
        next = "/?page="+str(page+1)
    elif page == last:
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)
    if page>last:
        return redirect(f"/?page={last}")
    return render_template('layout/home.html', title=params['website'],  params=params, posts=posts, prev=prev, next=next, module=datetime)

@app.route("/about")
def about():
    with open('config/about.txt') as a:
        params['about_text'] = a.read()
    return render_template('layout/about.html', title=f"{params['website']} - About", params=params)

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
            recipients = [authentication['gmail-user'], email],
            body = f"{message}\n\nPhone: {phone}"
        )
    
    return render_template('layout/contact.html', title=f"{params['website']} - Contact", params=params)


# *********************Posts*********************


class Posts(db.Model):
    """
    sno, title, slug, content, date
    """
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(6), nullable=True)
    img_file = db.Column(db.String(15), nullable=True)


class EmpthyPost:

    sno = title = tagline = slug = content = date = img_file = ""


@app.route("/posts")
def all_posts():
    posts = get_posts()
    return render_template('posts/posts.html', title=f"{params['website']} - Top Posts", params=params, posts=posts, module=datetime)

@app.route("/posts/<string:post_slug>", methods=["GET"])
def post_(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    post.date = datetime.strftime(post.date, "%B %d, %Y")
    return render_template('posts/post.html', title=post.title, params=params, post=post)

@app.route("/posts/old")
def old_posts():
    posts = get_posts()
    return render_template('posts/old.html', title=f"{params['website']} - Old Posts", params=params, posts=posts, module=datetime)

@app.route("/posts/next")
def next_posts():
    posts = get_posts()
    return render_template('posts/old.html', title=f"{params['website']} - Old Posts", params=params, posts=posts, module=datetime)

@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if (request.method == "POST"):
        if ('user' in session) and (session['user'] == admin['user-name']):
            file = request.files["file"]
            name = file.filename
            if name.endswith(".jpg") or name.endswith(".jpge") or name.endswith(".png"):
                folder = "images/"
            elif name.endswith(".txt"):
                folder = "docs/"
            else:
                return "The format is invalid"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], folder+secure_filename(name)))
            return "uploaded successfull"
    return redirect("/dashboard")

@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if ('user' in session) and (session['user'] == admin['user-name']):
        if (request.method=='POST'):
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('old_file')
            file = request.files['file']

            if (file.filename!='') and file.filename!=None:
                img_file = file.filename
                file_small = img_file.lower()
                if file_small.endswith(".jpg") or file_small.endswith(".jpeg") or file_small.endswith(".jpge") or file_small.endswith(".png"):
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(img_file)))
                else:
                    return "The format is invalid"

            if sno=="0":
                post = Posts(title=box_title, tagline=tagline, slug=slug, content=content, img_file=img_file, date=datetime.now())
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                print(img_file)
                post.img_file = img_file
                db.session.commit()
            return redirect(f"/posts/{slug}")

        post = Posts.query.filter_by(sno=sno).first()
        if post==None:
            post = EmpthyPost()
        return render_template("posts/edit.html", params=params, post=post, sno=sno)
    return redirect("/dashboard")

@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if ('user' in session) and (session['user'] == admin['user-name']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(debug=True)

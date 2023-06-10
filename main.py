import os
import requests
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
#db.create_all()

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publication_date = db.Column(db.String(10))
    isbn = db.Column(db.String(20), nullable=False, unique=True)
    num_pages = db.Column(db.Integer)
    cover_link = db.Column(db.String(200))
    language = db.Column(db.String(20))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search_books():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        language = request.form.get('language')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        books = Book.query
        if title:
            books = books.filter(Book.title.ilike(f'%{title}%'))
        if author:
            books = books.filter(Book.author.ilike(f'%{author}%'))
        if language:
            books = books.filter(Book.language.ilike(f'%{language}%'))
        if from_date:
            books = books.filter(Book.publication_date >= from_date)
        if to_date:
            books = books.filter(Book.publication_date <= to_date)

        books = books.all()

        return render_template('search.html', books=books)
    else:
        return render_template('search.html')

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        publication_date = request.form.get('publication_date')
        isbn = request.form.get('isbn')
        num_pages = request.form.get('num_pages')
        cover_link = request.form.get('cover_link')
        language = request.form.get('language')

        book = Book(
            title=title,
            author=author,
            publication_date=publication_date,
            isbn=isbn,
            num_pages=num_pages,
            cover_link=cover_link,
            language=language
        )

        db.session.add(book)
        db.session.commit()

        return redirect('/')
    else:
        return render_template('add_edit.html')

@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get(book_id)

    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.publication_date = request.form.get('publication_date')
        book.isbn = request.form.get('isbn')
        book.num_pages = request.form.get('num_pages')
        book.cover_link = request.form.get('cover_link')
        book.language = request.form.get('language')

        db.session.commit()

        return redirect('/')
    else:
        return render_template('add_edit.html', book=book)

@app.route('/delete', methods=['POST'])
def delete_book():
    book_id = request.form.get('book_id')
    book = Book.query.get(book_id)

    if book:
        db.session.delete(book)
        db.session.commit()

    return redirect('/')

@app.route('/import', methods=['GET'])
def import_books():
    keyword = request.args.get('keyword')

    if keyword:
        url = f'https://www.googleapis.com/books/v1/volumes?q={keyword}'
        response = requests.get(url)
        data = response.json()

        if 'items' in data:
            items = data['items']

            for item in items:
                volume_info = item.get('volumeInfo')
                title = volume_info.get('title')
                authors = volume_info.get('authors')
                publication_date = volume_info.get('publishedDate')
                isbn = volume_info.get('industryIdentifiers')[0].get('identifier')
                num_pages = volume_info.get('pageCount')
                cover_link = volume_info.get('imageLinks').get('thumbnail') if 'imageLinks' in volume_info else None
                language = volume_info.get('language')

                book = Book(
                    title=title,
                    author=', '.join(authors) if authors else None,
                    publication_date=publication_date,
                    isbn=isbn,
                    num_pages=num_pages,
                    cover_link=cover_link,
                    language=language
                )

                db.session.add(book)

            db.session.commit()

    books = Book.query.all()

    return render_template('import.html', books=books)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

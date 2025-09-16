from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/myapp')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Redis configuration
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

@app.route('/')
def hello():
    # Try to get data from cache first
    cached_users = redis_client.get('users_count')
    if cached_users:
        return f'Hello, World! (Cached) - Users in DB: {cached_users}'

    # If not in cache, query database
    try:
        user_count = User.query.count()
        # Cache the result for 60 seconds
        redis_client.setex('users_count', 60, user_count)
        return f'Hello, World! (From DB) - Users in DB: {user_count}'
    except Exception as e:
        return f'Hello, World! (DB Error: {str(e)})'

@app.route('/users')
def get_users():
    try:
        users = User.query.all()
        user_list = [{'id': u.id, 'name': u.name, 'email': u.email} for u in users]
        return {'users': user_list}
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)

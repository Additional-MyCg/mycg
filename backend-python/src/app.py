from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
from contextlib import contextmanager
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

@contextmanager
def get_db_cursor():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise e
    finally:
        if conn:
            conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        with get_db_cursor() as cursor:
            cursor.execute('SELECT NOW()')
            db_time = cursor.fetchone()[0]
        
        return jsonify({
            'service': 'python-backend',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'db_time': db_time.isoformat()
        })
    except Exception as e:
        return jsonify({
            'service': 'python-backend',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/products', methods=['GET'])
def get_products():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT * FROM products ORDER BY id')
            products = cursor.fetchall()
            return jsonify([{
                'id': p[0],
                'name': p[1],
                'price': float(p[2]),
                'created_at': p[3].isoformat() if p[3] else None
            } for p in products])
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        name = data.get('name')
        price = data.get('price')
        
        if not name or not price:
            return jsonify({'error': 'Name and price are required'}), 400
        
        with get_db_cursor() as cursor:
            cursor.execute(
                'INSERT INTO products (name, price) VALUES (%s, %s) RETURNING *',
                (name, price)
            )
            product = cursor.fetchone()
            
        return jsonify({
            'id': product[0],
            'name': product[1],
            'price': float(product[2]),
            'created_at': product[3].isoformat() if product[3] else None
        }), 201
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("🐍 Starting Python Flask server...")
    logger.info(f"🔗 Health check will be available at: /health")
    app.run(host='0.0.0.0', port=8000, debug=True)

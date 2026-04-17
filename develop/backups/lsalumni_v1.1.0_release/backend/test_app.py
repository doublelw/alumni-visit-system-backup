#!/usr/bin/env python3
"""
Minimal test Flask app to isolate the connection reset issue
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Test server is working!"

@app.route('/api/test')
def test_api():
    return jsonify({"message": "API is working"})

if __name__ == '__main__':
    print("Starting minimal test server...")
    app.run(host='0.0.0.0', port=5001, debug=True)
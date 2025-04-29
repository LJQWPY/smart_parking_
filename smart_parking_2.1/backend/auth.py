# auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import logging
import bcrypt
import sqlite3
from database import get_db_connection, init_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logging.warning(f"注册请求参数不全：username={username}")
        return jsonify({"msg": "用户名和密码不能为空"}), 400

    conn = None
    try:
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hashed_pw))
        conn.commit()
        logging.info(f"新用户注册成功：{username}")
        return jsonify({"msg": "注册成功"}), 201
    except sqlite3.IntegrityError:
        logging.warning(f"用户名已存在：{username}")
        return jsonify({"msg": "用户名已存在"}), 400
    except Exception as e:
        logging.error("注册发生未知错误：", exc_info=True)
        return jsonify({"msg": "服务器内部错误"}), 500
    finally:
        if conn:
            conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username =?", (username,))
        user = c.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"msg": "用户名或密码错误"}), 401
    except Exception as e:
        logging.error(f"登录出错: {str(e)}", exc_info=True)
        return jsonify({"msg": f"登录出错: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
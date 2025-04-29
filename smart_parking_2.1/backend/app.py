# app.py
from flask import Flask, Response, send_file, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from auth import auth_bp, init_db
from camera_manager import CameraManager
from detector import ParkingSpotDetector
import eventlet
import cv2
import logging
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

app = Flask(__name__, static_folder='../frontend/static')
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
    'JWT_ACCESS_TOKEN_EXPIRES': 3600,
    'JWT_TOKEN_LOCATION': ['headers', 'query_string'],
    'JWT_QUERY_STRING_NAME': 'token',
    'JWT_COOKIE_SECURE': True,
    'JWT_COOKIE_SAMESITE': 'Strict',
    'JWT_HEADER_NAME': 'Authorization',
})

jwt = JWTManager(app)
CORS(app, supports_credentials=True)
app.register_blueprint(auth_bp)

try:
    # 初始化摄像头管理器和检测模型
    camera_manager = CameraManager()
    detector = ParkingSpotDetector()
    logging.info("摄像头和车位检测模型初始化成功")
except Exception as e:
    logging.critical("初始化失败：", exc_info=True)
    exit(1)

@app.route('/')
def index():
    return send_file('../frontend/index.html')

@app.route('/video_feed/<int:cam_id>')
@jwt_required()
def video_feed(cam_id):
    try:
        if cam_id not in camera_manager.cameras:
            return jsonify({"error": "无效的摄像头ID"}), 404

        def generate():
            while True:
                frame = camera_manager.get_frame(cam_id)
                if frame is not None:
                    # 进行车位检测
                    detected_objects = detector.detect_objects(frame)
                    # 绘制检测框
                    for (x1, y1, x2, y2, class_id) in detected_objects:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f'ID:{class_id}', (x1, y1-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
                    # 编码为JPEG格式
                    _, buffer = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                eventlet.sleep(camera_manager.FRAME_INTERVAL)  # 按帧率控制间隔

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as e:
        logging.error(f"视频流错误: {str(e)}", exc_info=True)
        return jsonify({"error": "视频流获取失败"}), 500

@app.route('/available_cameras')
@jwt_required()
def available_cameras():
    active_cameras = []
    for cam_id in [0, 1, 2]:
        cap = cv2.VideoCapture(cam_id, camera_manager.backend)
        if cap.isOpened():
            active_cameras.append(cam_id)
            cap.release()
    return jsonify({
        "available_cameras": active_cameras,
        "current_camera": 0
    })

@app.route('/toggle_camera/<int:cam_id>', methods=['POST'])
@jwt_required()
def toggle_camera(cam_id):
    camera_manager.toggle_camera(cam_id)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    with app.app_context():
        init_db()

    import eventlet
    eventlet.monkey_patch(
        os=True,
        select=True,
        socket=True,
        thread=True,
        time=True
    )

    from eventlet import wsgi

    print("Server running on http://localhost:5000")
    wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
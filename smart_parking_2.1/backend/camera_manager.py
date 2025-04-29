# camera_manager.py
import cv2
import logging
import os
import time

class CameraManager:
    MAX_CAMERA_ATTEMPTS = 3
    FRAME_RATE = 30
    FRAME_INTERVAL = 1 / FRAME_RATE

    def __init__(self):
        self.cameras = {}
        self.backend = self.get_backend()
        self.initialize_cameras()
        logging.info(f"可用摄像头列表: {list(self.cameras.keys())}")

    def get_backend(self):
        if os.name == 'nt':
            if cv2.videoio_registry.hasBackend(cv2.CAP_DSHOW):
                return cv2.CAP_DSHOW
        return cv2.CAP_ANY

    def initialize_cameras(self):
        try:
            logging.info(f"正在使用 {self.backend} 后端初始化摄像头...")
            for cam_id in [0, 1, 2]:
                if self.test_camera(cam_id):
                    cap = cv2.VideoCapture(cam_id, self.backend)
                    cap.set(cv2.CAP_PROP_FPS, self.FRAME_RATE)
                    self.cameras[cam_id] = cap
            if not self.cameras:
                raise RuntimeError("未检测到可用摄像头")
        except Exception as e:
            logging.error(f"摄像头初始化失败: {str(e)}", exc_info=True)
            raise

    def test_camera(self, cam_id):
        cap = cv2.VideoCapture(cam_id, self.backend)
        if cap.isOpened():
            logging.info(f"摄像头 {cam_id} 检测成功")
            cap.release()
            return True
        return False

    def check_camera_status(self, cam_id):
        if cam_id not in self.cameras:
            return False
        return self.cameras[cam_id].isOpened()

    def get_frame(self, cam_id):
        if cam_id not in self.cameras or not self.check_camera_status(cam_id):
            logging.warning(f"摄像头 {cam_id} 连接异常，启动重连")
            success = self.reconnect(cam_id)
            if not success:
                return None

        cap = self.cameras[cam_id]
        try:
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
            ret, frame = cap.read()
            if ret:
                return frame
            else:
                self.reconnect(cam_id)
                ret, frame = cap.read()
                return frame if ret else None
        except Exception as e:
            logging.error(f"摄像头 {cam_id} 读帧失败: {str(e)}", exc_info=True)
            self.reconnect(cam_id)
            return None

    def reconnect(self, cam_id):
        max_attempts = 3
        for attempt in range(max_attempts):
            logging.info(f"尝试重新连接摄像头 {cam_id}（第{attempt+1}次）")
            if cam_id in self.cameras:
                self.cameras[cam_id].release()
            cap = cv2.VideoCapture(cam_id, self.backend)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FPS, self.FRAME_RATE)
                self.cameras[cam_id] = cap
                logging.info(f"摄像头 {cam_id} 重连成功")
                return True
            time.sleep(1)
        logging.error(f"摄像头 {cam_id} 重连失败")
        return False

    def check_stream_health(self, cam_id):
        test_frames = 5
        error_count = 0
        for _ in range(test_frames):
            frame = self.get_frame(cam_id)
            if frame is None:
                error_count += 1
        return error_count < 2

    def toggle_camera(self, cam_id):
        if cam_id in self.cameras:
            if self.cameras[cam_id].isOpened():
                self.cameras[cam_id].release()
                del self.cameras[cam_id]
                logging.info(f"摄像头 {cam_id} 已关闭")
            else:
                if self.test_camera(cam_id):
                    self.cameras[cam_id] = cv2.VideoCapture(cam_id, self.backend)
        else:
            if self.test_camera(cam_id):
                self.cameras[cam_id] = cv2.VideoCapture(cam_id, self.backend)

    def __del__(self):
        for cam_id, cap in self.cameras.items():
            try:
                cap.release()
                logging.info(f"摄像头 {cam_id} 资源已释放")
            except Exception as e:
                logging.error(f"释放摄像头 {cam_id} 资源失败: {str(e)}")
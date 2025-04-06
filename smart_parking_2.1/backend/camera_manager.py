import cv2
import logging


class CameraManager:
    MAX_CAMERA_ATTEMPTS = 10  # 设置最大尝试次数

    def __init__(self):
        """
        初始化摄像头管理器，尝试打开所有可用的摄像头设备
        """
        self.cameras = {}
        try:
            logging.info("开始初始化摄像头管理器")
            cam_id = 0
            while cam_id < self.MAX_CAMERA_ATTEMPTS:
                cap = cv2.VideoCapture(cam_id)
                if cap.isOpened():
                    self.cameras[cam_id] = cap
                    logging.info(f"成功打开摄像头 {cam_id}")
                    cam_id += 1
                else:
                    if cam_id == 0:
                        logging.error("未检测到可用的摄像头，请检查设备连接。")
                        raise ValueError("未检测到可用的摄像头，请检查设备连接。")
                    break
            logging.info("摄像头管理器初始化成功")
        except Exception as e:
            logging.error(f"摄像头管理器初始化失败: {str(e)}")
            raise

    def get_frame(self, cam_id):
        """
        从指定的摄像头获取视频帧
        :param cam_id: 摄像头的 ID
        :return: 视频帧，如果获取失败则返回 None
        """
        logging.info(f"开始获取摄像头 {cam_id} 的视频帧")
        cap = self.cameras.get(cam_id)
        if cap:
            try:
                ret, frame = cap.read()
                if ret:
                    # 这里可以添加视频帧的预处理逻辑，如调整大小、编码等
                    logging.info(f"成功获取摄像头 {cam_id} 的视频帧")
                    return frame
                else:
                    logging.info(f"无法从摄像头 {cam_id} 获取视频帧")
            except Exception as e:
                logging.error(f"获取摄像头 {cam_id} 的视频帧出错: {str(e)}")
        return None

    def toggle_camera(self, cam_id):
        """
        切换指定摄像头的开关状态
        :param cam_id: 摄像头的 ID
        """
        logging.info(f"开始切换摄像头 {cam_id} 的开关状态")
        cap = self.cameras.get(cam_id)
        if cap:
            try:
                if cap.isOpened():
                    cap.release()
                    del self.cameras[cam_id]
                    logging.info(f"已关闭摄像头 {cam_id}")
                else:
                    cap = cv2.VideoCapture(cam_id)
                    if cap.isOpened():
                        self.cameras[cam_id] = cap
                        logging.info(f"已打开摄像头 {cam_id}")
                    else:
                        logging.error(f"无法打开摄像头 {cam_id}")
            except Exception as e:
                logging.error(f"切换摄像头 {cam_id} 的开关状态出错: {str(e)}")
        else:
            logging.error(f"未找到摄像头 {cam_id}")

    def __del__(self):
        """
        析构函数，在对象销毁时释放所有摄像头资源
        """
        for cam_id, cap in self.cameras.items():
            try:
                cap.release()
                logging.info(f"已释放摄像头 {cam_id} 的资源")
            except Exception as e:
                logging.error(f"释放摄像头 {cam_id} 的资源出错: {str(e)}")

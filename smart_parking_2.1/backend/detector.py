import cv2
import torch
import os
from ultralytics import YOLO
import logging
from torch.nn.modules.container import Sequential
from ultralytics.nn.tasks import DetectionModel


class ParkingSpotDetector:
    def __init__(self, model_path=r'E:\bc\python\smart_parking_2.1\yolov8n.pt'):
        try:
            # 安全配置（兼容PyTorch 2.0+）
            if hasattr(torch.serialization, '_weights_only'):
                torch.serialization._weights_only = False

            # 验证模型文件
            logging.info(f"模型文件路径: {os.path.abspath(model_path)}")
            if not os.path.isfile(model_path):
                raise FileNotFoundError(f"模型文件不存在: {model_path}")

            # 初始化模型
            self.device = 0 if torch.cuda.is_available() else 'cpu'
            logging.info(f"使用计算设备: {'GPU' if self.device == 0 else 'CPU'}")
            self.model = YOLO(model_path)
            self.model.to(self.device)

            # 模型预热（关键修改）
            dummy_frame = torch.zeros((1, 3, 640, 640), dtype=torch.float32)  # BCHW格式
            self.model.predict(dummy_frame, verbose=False)
            logging.info("YOLOv8模型加载成功")

        except Exception as e:
            logging.critical(f"模型初始化失败: {str(e)}", exc_info=True)
            raise

    def detect_objects(self, frame):
        """
        执行目标检测
        :param frame: 输入BGR图像帧
        :return: 检测结果列表 [(x1, y1, x2, y2, class_id), ...]
        """
        try:
            if frame is None or frame.size == 0:
                logging.warning("接收到空帧")
                return []

            # 预处理流程
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 转换为BCHW格式并归一化
            input_tensor = torch.from_numpy(rgb_frame).float()
            input_tensor = input_tensor.permute(2, 0, 1).unsqueeze(0) / 255.0  # HWC -> BCHW

            # 执行推理
            results = self.model.predict(input_tensor, verbose=False)

            # 解析结果
            detected_objects = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    detected_objects.append((x1, y1, x2, y2, class_id))

            return detected_objects

        except Exception as e:
            logging.error(f"检测失败: {str(e)}", exc_info=True)
            return []
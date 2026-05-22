import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

class GateCalibrator(Node):
    def __init__(self):
        super().__init__('gate_calibrator')
        # Load your model
        self.model = YOLO('/home/mahmmudqatmh/ros2_ws/src/my_tello_vision/models/best.pt')
        self.bridge = CvBridge()
        
        # Subscription to Tello Camera
        self.sub = self.create_subscription(Image, '/image_raw', self.listener_callback, 10)
        
        self.get_logger().info("--- CALIBRATOR READY ---")
        self.get_logger().info("Hold the drone at the exact center of the gate.")

    def listener_callback(self, data):
        img = self.bridge.imgmsg_to_cv2(data, "bgr8")
        h, w, _ = img.shape
        img_center_x, img_center_y = w // 2, h // 2
        
        results = self.model(img, conf=0.5, verbose=False)
        
        # Draw Image Center Crosshair (Blue)
        cv2.drawMarker(img, (img_center_x, img_center_y), (255, 0, 0), cv2.MARKER_CROSS, 20, 2)

        if results[0].boxes:
            # Get the largest box
            box = max(results[0].boxes, key=lambda b: (b.xyxy[0][2]-b.xyxy[0][0]) * (b.xyxy[0][3]-b.xyxy[0][1]))
            x1, y1, x2, y2 = box.xyxy[0]
            
            gate_center_x = int((x1 + x2) / 2)
            gate_center_y = int((y1 + y2) / 2)

            # Calculate Offsets
            offset_x = gate_center_x - img_center_x
            offset_y = gate_center_y - img_center_y # Positive means gate is lower than camera center

            # Draw Gate Center (Green)
            cv2.drawMarker(img, (gate_center_x, gate_center_y), (0, 255, 0), cv2.MARKER_TILTED_CROSS, 20, 2)
            # Draw line between them
            cv2.line(img, (img_center_x, img_center_y), (gate_center_x, gate_center_y), (0, 255, 255), 2)

            # Display Data on Screen
            text = f"X Offset: {offset_x} | Y Offset: {offset_y}"
            cv2.putText(img, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Print to terminal for easy copying
            print(f"CALIBRATION DATA -> X: {offset_x}, Y: {offset_y}")

        cv2.imshow("Gate Calibration Tool", img)
        cv2.waitKey(1)

def main():
    rclpy.init()
    node = GateCalibrator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
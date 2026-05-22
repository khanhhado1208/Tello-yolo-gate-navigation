import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import datetime
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class TelloYoloRecorder(Node):
    def __init__(self):
        super().__init__('tello_yolo_recorder')
        self.bridge = CvBridge()
        self.model = YOLO('/home/mahmmudqatmh/ros2_ws/src/my_tello_vision/models/best.pt')
        
        # MATCH THE TELLO DRIVER QoS
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.listener_callback,
            qos)
        
        self.video_writer = None
        self.filename = f"tello_yolo_flight_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        self.get_logger().info(f"Recording WITH YOLO to: {self.filename}")

    def listener_callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            results = self.model(cv_image, conf=0.45, verbose=False)
            annotated_frame = results[0].plot()

            if self.video_writer is None:
                height, width, _ = annotated_frame.shape
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(self.filename, fourcc, 30.0, (width, height))
                self.get_logger().info("Recording started successfully!")

            self.video_writer.write(annotated_frame)
            cv2.imshow("YOLO Recording Preview", annotated_frame)
            cv2.waitKey(1)
        except Exception as e:
            self.get_logger().error(f"Error during recording: {e}")

    def stop_recording(self):
        if self.video_writer is not None:
            self.video_writer.release()
            cv2.destroyAllWindows()
            self.get_logger().info(f"Video saved: {self.filename}")

def main(args=None):
    rclpy.init(args=args)
    node = TelloYoloRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_recording()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
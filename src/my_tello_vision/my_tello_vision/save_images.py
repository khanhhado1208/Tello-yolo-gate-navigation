import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import cv2
import os

class ImageSaver(Node):
    def __init__(self):
        super().__init__('image_saver')
        
        # 1. Define the QoS Profile to match the Tello Driver
        # This fixes the 'incompatible QoS' warning
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # 2. Subscribe using the profile
        # Change '/image_raw' to '/image' if your topic list shows something else
        self.subscription = self.create_subscription(
            Image, 
            '/image_raw', 
            self.listener_callback, 
            qos_profile)
        
        self.bridge = CvBridge()
        self.count = 0
        
        # Create folder if it doesn't exist
        if not os.path.exists('tello_images'):
            os.makedirs('tello_images')
            self.get_logger().info('Created folder: tello_images')

    def listener_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Show the live feed window
            cv2.imshow("Tello Live Feed", cv_image)
            
            # Check if 'q' is pressed on the window to stop early
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info('Closing window...')
                cv2.destroyAllWindows()
            
            # Save every 10th frame to avoid too many duplicate images
            # You can change 10 to 20 if you want fewer, sharper images
            if self.count % 10 == 0:
                file_name = f'tello_images/frame_{self.count}.jpg'
                cv2.imwrite(file_name, cv_image)
                self.get_logger().info(f'Saved: {file_name}')
            
            self.count += 1
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')

def main(args=None):
    rclpy.init(args=args)
    image_saver = ImageSaver()
    
    self_logger = rclpy.logging.get_logger('main')
    self_logger.info('Image Saver Node Started. Press Ctrl+C to stop.')
    
    try:
        rclpy.spin(image_saver)
    except KeyboardInterrupt:
        self_logger.info('Shutting down...')
    finally:
        cv2.destroyAllWindows()
        image_saver.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

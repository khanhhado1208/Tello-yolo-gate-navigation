import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from ultralytics import YOLO
import time, cv2, math, os
from tello_msgs.srv import TelloAction 
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class PID:

## Tuning the PID parameter
## kp: high kp makes the drone move fast to correct an error but too high causes shaking
## kd: the brakes It predicts future error to prevent the drone from overshooting.
    def __init__(self, kp, ki, kd):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.prev_error = 0
        self.integral = 0
    def update(self, error, dt):
        if dt <= 0: return 0
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.prev_error = error
        return output
    def reset(self):
        self.prev_error = 0
        self.integral = 0

class TelloFSMRunner(Node):
    def __init__(self):
        super().__init__('tello_fsm_runner')
        
        # Expands the '~' to the actual home directory of whoever is running the code
        self.model = YOLO('/home/hado/ros2_ws/src/ros2_ws/src/my_tello_vision/models/best.pt')
        
        self.bridge = CvBridge()
        
        self.state = 0 
        self.gate_count = 0
        self.total_gates = 4 # Full mission
        
        self.state_start_time = time.time()
        self.last_gate_seen_time = time.time()
        self.last_known_err_x = 0.0
        self.last_known_err_y = 0.0
        
        # High-Precision PID Settings
        self.pid_yaw = PID(kp=0.0036, ki=0.0, kd=0.0008)
        self.pid_z = PID(kp=0.0066, ki=0.0, kd=0.0012)
        
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(Image, '/image_raw', self.frame_callback, 
            QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=1))
        self.tello_client = self.create_client(TelloAction, '/tello_action')
        
        self.last_time = time.time()
        self.mission_active = False
        self.create_timer(2.0, self.attempt_takeoff)

    def attempt_takeoff(self):
        if self.mission_active: return
        if self.tello_client.wait_for_service(timeout_sec=0.5):
            self.tello_client.call_async(TelloAction.Request(cmd="takeoff"))
            self.mission_active = True
            self.state_start_time = time.time() + 4.0 # Here I reduced the takeoff wait 

    def frame_callback(self, data):
        if not self.mission_active or time.time() < self.state_start_time: return
        
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        img = self.bridge.imgmsg_to_cv2(data, "bgr8")
        results = self.model(img, conf=0.45, verbose=False)
        h_img, w_img, _ = img.shape
        cmd = Twist()

        target = None
        if results[0].boxes:
            if self.gate_count < self.total_gates:
                gates = [b for b in results[0].boxes if "stop" not in self.model.names[int(b.cls[0])].lower()]
                if gates:
                    target = max(gates, key=lambda b: (b.xyxy[0][2]-b.xyxy[0][0]) * (b.xyxy[0][3]-b.xyxy[0][1]))
            else:
                stops = [b for b in results[0].boxes if "stop" in self.model.names[int(b.cls[0])].lower()]
                if stops: target = stops[0]

        # --- FSM LOGIC ---
        if self.state == 0: # SEARCH
            if target:
                self.state = 1
                self.pid_yaw.reset()
                self.pid_z.reset()

            else:
                # Here I define blind maneuvering: Force turn toward Gate 3 if we just passed Gate 2
                elapsed = now - self.state_start_time
                if self.gate_count == 2:
                    if elapsed < 1.2: # Time to turn ~80 deg
                        cmd.angular.z = -0.7 # Fast Right Turn
                    elif elapsed < 2.5: # Move forward ~1 meter
                        cmd.linear.x = 0.25 
                        cmd.angular.z = 0.0
                    else: # Resume normal search if not found yet
                        cmd.angular.z = -0.4
                else:
                    search_elapsed = now - self.state_start_time
                    cmd.angular.z = -0.60 * math.sin(search_elapsed * 2.2)
                    if cmd.angular.z > 0: cmd.angular.z *= 0.15 

        elif self.state == 1: # Aign
            if not target:
                self.state = 5 # Recovery
                self.state_start_time = now
            else:
                self.last_gate_seen_time = now
                x1, y1, x2, y2 = target.xyxy[0]
                w_box = x2 - x1
                
                f_vel = 0.25 
                base_comp = (f_vel * 250)
                
                # RE-CALIBRATED: 1.55 Tilt & 0.15 Right-Bias
                tilt = base_comp * 3.1
                dynamic_cx = (w_img * 0.5) + (tilt * 0.14)
                dynamic_cy = (h_img * 0.5) - tilt
                
                self.last_known_err_x = ((x1 + x2) / 2) - dynamic_cx
                self.last_known_err_y = ((y1 + y2) / 2) - dynamic_cy
                
                cmd.angular.z = float(max(min(-self.pid_yaw.update(self.last_known_err_x, dt), 0.50), -0.50))
                cmd.linear.z = float(max(min(-self.pid_z.update(self.last_known_err_y, dt), 0.60), -0.60))
                cmd.linear.x = f_vel

                # Strict Punch condition for consecutive gates
                if w_box > (w_img * 0.38) and abs(self.last_known_err_x) < 30 and abs(self.last_known_err_y) < 30:
                    self.get_logger().info(f"Gate {self.gate_count + 1} Centered. Executing Punch.")
                    self.state = 2
                    self.state_start_time = now

        elif self.state == 5: # RECOVERY (Memory Mode)
            if target: self.state = 1
            elif now - self.state_start_time > 2.0:
                self.state = 0
                self.state_start_time = now
            else:
                cmd.angular.z = float(max(min(-self.pid_yaw.update(self.last_known_err_x, dt), 0.30), -0.30))
                cmd.linear.z = 0.10 
                cmd.linear.x = 0.10

        elif self.state == 2: # PENETRATE (The Punch)
            # We can Reduce the punch duration for gate 1, 3, 4 to save time 
            #punch_limit = 4.0 if self.gate_count == 3 else 3
            if now - self.state_start_time < 3.6: # 2.5s for deep clearance #punch_limit:
                cmd.linear.x = 0.40
                cmd.linear.z = 0.07 # Tiny lift to prevent sag
                cmd.angular.z = 0.0
            else:
                self.state = 3
                self.state_start_time = now

        elif self.state == 3: # BRAKE & COUNT
            brake_duration = 0.4  # Reduce the break time
            climb_duration = 1.3  # Reduce the climb time
            
            if now - self.state_start_time < brake_duration:
                cmd.linear.x = -0.20 # Braking
            # Elevation boost: Only triggers after the 4th gate (gate_count is still 3 here)
            elif self.gate_count == 3 and (now - self.state_start_time < brake_duration + climb_duration):
                cmd.linear.z = 0.50 # Elevation boost for 50-60 cm we can force aggressive climb 0.45
                cmd.linear.x = 0.0
            else:
                self.gate_count += 1
                self.get_logger().info(f"Progress: {self.gate_count}/{self.total_gates}")
                self.state = 4 if self.gate_count >= self.total_gates else 0
                self.state_start_time = now

        elif self.state == 4: # LAND (Final Target: Stop Sign)
            if target:
                x1, y1, x2, y2 = target.xyxy[0]
                if (x2 - x1) > (w_img * 0.18):
                    self.tello_client.call_async(TelloAction.Request(cmd="land"))
                else:
                    cmd.linear.x = 0.20 # For faster approach to stop sign 0.25
            else:
                cmd.linear.x = 0.0
                cmd.angular.z = -0.30  # For Faste spin to stopo sing -0.4

        self.pub.publish(cmd)
        cv2.imshow("Aerial Robot - Full Mission", results[0].plot())
        cv2.waitKey(1)

def main():
    rclpy.init(); node = TelloFSMRunner()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__': main()
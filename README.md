# Tello YOLO Gate Navigation

Autonomous ROS 2 vision-based navigation for a DJI/Ryze Tello drone using YOLO gate detection and PID control.

## Demo

![Tello gate navigation preview](media/tello_gate_navigation_preview.gif)

Full demo: [tello_gate_navigation_demo.mp4](media/tello_gate_navigation_demo.mp4)

## Features

- ROS 2 Humble
- Tello drone control using `/cmd_vel`
- YOLO gate and stop-sign detection
- PID-based yaw and altitude alignment
- Finite State Machine:
  - Search
  - Align
  - Penetrate gate
  - Brake
  - Recovery
  - Land
- Demo recording of the drone flying through all gates and stopping at the stop sign

## Project Structure

```text
src/
├── my_tello_vision/
│   ├── launch/              # ROS 2 launch files
│   ├── models/              # YOLO weights (best.pt)
│   ├── my_tello_vision/     # Core Python logic: FSM, PID, vision control
│   ├── simulation/          # Gazebo world/course files
│   ├── package.xml          # ROS 2 package metadata
│   └── setup.py             # Python package setup and entry points
├── tello_ros2_humble_driver/
│   └── tello_ros/           # Tello driver, messages, and Gazebo support
media/
├── tello_gate_navigation_preview.gif
└── tello_gate_navigation_demo.mp4
```

## Main Control Node

```text
src/my_tello_vision/my_tello_vision/tello_vision_control.py
```

## Requirements

- Ubuntu 22.04
- ROS 2 Humble
- Python 3
- OpenCV
- cv_bridge
- Ultralytics YOLO
- Tello ROS 2 driver
- DJI/Ryze Tello drone

Install Python dependencies:

```bash
pip install ultralytics opencv-python
```

Install Tello driver dependency:

```bash
sudo apt install libh264-dev
```

## Clone

Clone this repository into a ROS 2 workspace:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/khanhhado1208/Tello-yolo-gate-navigation.git
```

## Build

```bash
cd ~/ros2_ws
colcon build
source install/setup.bash
```

## Running the Mission

Open a new terminal for each step.

### Step 1: Connect to Tello Wi-Fi

Power on the DJI/Ryze Tello drone, then connect your computer to the drone’s Wi-Fi network.

### Step 2: Launch the Tello Driver

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch tello_driver tello_driver.launch.py
```

If the launch file name is different in your driver version, check available launch files with:

```bash
find src/tello_ros2_humble_driver -name "*.launch.py"
```

### Step 3: Run the Autonomous Vision Controller

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 run my_tello_vision tello_vision_control
```

### Optional: Record the Tello Camera Stream

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 run my_tello_vision record_tello
```

## Navigation Logic

The drone uses a finite state machine for autonomous gate navigation.

1. **SEARCH**  
   Searches for the next gate or stop sign using the camera feed and YOLO detections.

2. **ALIGN**  
   Uses PID control to align the drone with the detected gate center.

3. **PENETRATE**  
   Moves forward through the gate with a small upward command to reduce altitude sag.

4. **BRAKE**  
   Applies a short braking motion after passing a gate.

5. **RECOVERY**  
   Uses the last known target direction if the gate is temporarily lost.

6. **LAND**  
   Approaches and lands after detecting the stop sign.

## Control Strategy

The controller combines:

- YOLO-based gate and stop-sign detection
- PID yaw correction for horizontal alignment
- PID altitude correction for vertical alignment
- Forward velocity control for gate approach
- A finite state machine for mission sequencing
- Conservative speed and tolerance values for low-cost Tello flight stability

## Reliability Notes

This project was tested on a low-cost DJI/Ryze Tello drone in an indoor gate course. Flight behavior can vary between runs because of battery level, motor temperature, Wi-Fi/video latency, lighting, and accumulated drift after each gate.

A fully charged battery may make the drone more aggressive because the same velocity commands can produce stronger movement. After several retries, the drone may behave more smoothly as battery voltage drops, but very low battery can also cause altitude sag.

For best repeatability:

- Use consistent battery level during testing
- Keep lighting and gate placement unchanged
- Let the drone stabilize before each run
- Avoid over-tuning for one single successful attempt
- Use moderate speeds and loose gate-center tolerance instead of strict centering

## Notes

The controller is tuned for a simple indoor gate course with four gates and a stop sign. Performance may change depending on the physical setup and Tello flight conditions.
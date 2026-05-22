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

## Project Structure

```text
src/
├── my_tello_vision/
└── tello_ros2_humble_driver/
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

## Build

```bash
cd ~/ros2_ws
colcon build
source install/setup.bash
```

## Run

```bash
ros2 run my_tello_vision tello_vision_control
```

## Notes

This project was tested on a low-cost Tello drone, so the controller uses soft PID limits, loose gate-center tolerance, and moderate forward speed for stable gate passing.


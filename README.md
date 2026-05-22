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
- DJI/Ryze Tello drone

## Clone

```bash
git clone https://github.com/khanhhado1208/Tello-yolo-gate-navigation.git
cd Tello-yolo-gate-navigation
```

## Build

```bash
colcon build
source install/setup.bash
```

## Run

First, connect your computer to the Tello Wi-Fi network.

Then start the Tello driver in one terminal:

```bash
source install/setup.bash
ros2 launch tello_driver tello_driver.launch.py
```

In another terminal, run the vision controller:

```bash
source install/setup.bash
ros2 run my_tello_vision tello_vision_control
```
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
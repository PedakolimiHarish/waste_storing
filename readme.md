# Waste Sorting Robotic Workcell

A ROS 2 Jazzy and Gazebo-based robotic waste sorting simulation consisting of four UR10e robotic arms equipped with Robotiq 2F-85 grippers.

The workcell simulates a conveyor-based waste sorting system in which waste objects are transported along a conveyor and assigned to different robotic stations for sorting.

## Main Components

- 4 × Universal Robots UR10e

- 4 × Robotiq 2F-85 parallel grippers

- 1 × conveyor belt

- Plastic (Blue Bins) and metal (Gray Bins) waste sorting bins

- Robot work tables

- Gazebo Harmonic simulation environment

- MoveIt 2 motion planning

- `ros2_control` robot control

- Custom ROS 2 workcell launch and configuration


## Simulation Architecture

```text
                    Waste Sorting Workcell

                         Waste Objects
                               │
                               ▼
                        ┌─────────────┐
                        │  Conveyor   │
                        └─────────────┘
                               │
             ┌─────────────────┼─────────────────┐─────────────┐
             │                 │                 │             │
             ▼                 ▼                 ▼             ▼
           Robot 1           Robot 2           Robot 3      Robot 4
             │                 │                 │             │
          UR10e             UR10e             UR10e         UR10e
             │                 │                 │             │
        Robotiq 2F-85     Robotiq 2F-85     Robotiq 2F-85  Robotiq 2F-85
             │                 │                 │             │
        Plastic/Metal     Plastic/Metal     Plastic/Metal  Plastic/Metal
             │                 │                 │             │
             └─────────────────┴─────────────────┴─────────────┘
```

The simulation is intended as the foundation for a complete autonomous waste sorting system, including object detection, tracking, robotic picking, classification, and placement.

---
# Environment

The project is developed and tested using **Docker Desktop with WSL2**. The ROS 2 workspace runs inside an Ubuntu-based Docker container.

## Host Environment

- **Host OS:** Windows

- **Linux environment:** Ubuntu on WSL2

- **Container runtime:** Docker Desktop

- **Source workspace:** `~/ros2/src`


## Docker Environment

The Docker environment is defined by the repository:

```text
docker/
├── Dockerfile
└── docker-compose.yml
```

The container provides the ROS 2 development and simulation environment.

## ROS 2 Environment

- **Ubuntu:** 24.04

- **ROS 2:** Jazzy

- **Gazebo:** Gazebo Harmonic / Gazebo Sim 8

- **MoveIt:** MoveIt 2

- **Control:** `ros2_control`

- **Build system:** `colcon`

- **Dependency management:** `rosdep`


## Robotic System

The simulated workcell consists of:

```text
4 × Universal Robots UR10e
4 × Robotiq 2F-85 grippers
1 × conveyor belt
Plastic waste bins (Blue)
Metal waste bins (Gray)
Robot work tables
```

## ROS 2 Packages

The workspace contains the packages required for:

- Universal Robots simulation

- UR10e robot description and controllers

- MoveIt configuration

- Robotiq grippers

- Conveyor belt simulation

- Custom waste-sorting workcell

---
# Repository & Workspace Setup

Create the ROS 2 source workspace in WSL2:

```bash
mkdir -p ~/ros2/src
cd ~/ros2
```

Clone the repository directly into the `src` directory:

```bash
git clone https://github.com/PedakolimiHarish/waste_sorting.git src
```

The ROS 2 source workspace should then contain the individual packages directly under `src`:

```text
~/ros2/
└── src/
    ├── robot_workcell/
    ├── ur_description/
    ├── ur_msgs/
    ├── ur_client_library/
    ├── ur_controllers/
    ├── ur_moveit_config/
    ├── ur_simulation_gz/
    ├── conveyorbelt_gz/
    ├── conveyorbelt_msgs/
    ├── ros2_conveyorbelt/
    ├── robotiq_description/
    ├── robotiq_controllers/
    ├── robotiq_driver/
    └── ...
```

The Docker configuration is part of the repository:

```text
~/ros2/src/docker/
├── Dockerfile
└── docker-compose.yml
```

After cloning, verify the source directory:

```bash
cd ~/ros2/src
ls
```

Navigate to the Docker directory:

```bash
cd ~/ros2/src/docker
```

The directory contains:

```text
docker/
├── Dockerfile
└── docker-compose.yml
```

Build the Docker image and start the container:

```bash
docker compose up --build
```

To start the container in detached mode:

```bash
docker compose up --build -d
```

---
# VS Code Dev Container Setup

This project uses **Visual Studio Code with the Dev Containers extension** to develop directly inside the running Docker container.

## 1. Install VS Code

Install Visual Studio Code on the host machine.

## 2. Install the Dev Containers Extension

Open VS Code and install:

**Dev Containers**

from the VS Code Extensions marketplace.

## 3. Start the Docker Container

From WSL2:

```bash
cd ~/ros2/src/docker
docker compose up --build
```

Make sure the `waste-sorting` container is running before continuing. you can start it from Docker Desktop

## 4. Attach VS Code to the Running Container

In VS Code:

1. Press:


```text
Ctrl + Shift + P
```

2. Search for:


```text
Dev Containers: Attach to Running Container
```

3. Select:


```text
waste-sorting
```

4. VS Code will open a **new window** connected directly to the running Docker container.


## 5. Open the ROS 2 Workspace

In the new VS Code container window, open:

```text
/home/ubuntu/ros2_ws
```

The integrated terminal now runs **inside the Docker container**, so ROS 2 commands can be executed directly from VS Code.

You can verify the environment with:

```bash
source /opt/ros/jazzy/setup.bash
```

and:

```bash
source ~/ros2_ws/install/setup.bash
```
---
# ROS 2 Setup Inside Docker

Enter the Docker container and source ROS 2 Jazzy:

```bash
source /opt/ros/jazzy/setup.bash
```

Navigate to the ROS 2 workspace:

```bash
cd ~/ros2_ws
```

The source packages should be available under:

```text
~/ros2_ws/src/
```

Verify:

```bash
ls ~/ros2_ws/src
```

---

# Install System Dependencies

Update the package index:

```bash
sudo apt-get update
```

Install Bullet dependencies:

```bash
cd ~/ros2_ws
sudo apt-get install -y \
  libbullet-dev \
  libbullet-extras-dev
```

---

# Install ROS Dependencies

Update rosdep:

```bash
rosdep update
```

Install dependencies for all packages in the workspace:

```bash
cd ~/ros2_ws
rosdep install \
  --from-paths src \
  --ignore-src \
  --rosdistro jazzy \
  -r \
  -y
```

The `-r` option allows rosdep to continue when an individual dependency cannot be resolved.

---

# Build the Workspace

Build the complete workspace:

```bash
cd ~/ros2_ws
colcon build \
  --symlink-install \
  --parallel-workers 1
```

Using one worker reduces resource usage when building the complete workspace inside Docker.

After a successful build:

```bash
RUN echo "source ~/ros2_ws/install/setup.bash" >> /home/ubuntu/.bashrc
```
---
# Optional UR10e Standalone Test

The upstream Universal Robots simulation can be tested independently before starting the custom workcell.

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch ur_simulation_gz ur_sim_control.launch.py \
  ur_type:=ur10e
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch ur_simulation_gz ur_sim_moveit.launch.py \
  ur_type:=ur10e
```

This test is optional and is not required for running the final waste-sorting workcell.

---

# Workcell Launch Files

The custom workcell contains the following main launch files:

```text
launch/
├── ur_workcell_robot.launch.py
├── ur_workcell_moveit_robot.launch.py
├── workcell_gazebo.launch.py
└── workcell_moveit.launch.py
```

### `ur_workcell_robot.launch.py`

Starts one UR10e robot, its `ros2_control` system, and its controllers.

The robot includes a Robotiq 2F-85 gripper.

### `ur_workcell_moveit_robot.launch.py`

Starts the MoveIt backend for one robot.

### `workcell_world.launch.py`

Starts only the Gazebo workcell environment without the four robots.

This is useful when modifying:

- workcell layout

- conveyor

- tables

- sorting bins

- environment models


### `workcell_gazebo.launch.py`

Starts the complete simulated workcell with:

- four UR10e robots

- four Robotiq 2F-85 grippers

- conveyor belt

- tables

- plastic bins

- metal bins

- Gazebo environment

- robot controllers


The conveyor is automatically started by this launch file.

### `workcell_moveit.launch.py`

Starts the MoveIt backend for all four robots.

---

# Start the Gazebo World Only

To start Gazebo without the four robots:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch robot_workcell workcell_world.launch.py
```

This mode is intended for developing and modifying the simulated workcell.

---

# Start the Complete 4 Robot Gazebo Workcell

For the complete simulation, use:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch robot_workcell workcell_gazebo.launch.py
```

This starts the complete four-robot simulation.

The robots are started sequentially so that each robot's controllers are ready before the next robot is started.

The conveyor is also commanded to start automatically at 100% power.

---

# Start the single Robot Gazebo Workcell

For the complete simulation, use:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

 ros2 launch robot_workcell single_robot_gazebo.launch.py
```

This starts the complete single-robot simulation.

The conveyor is also commanded to start automatically at 100% power.

---

# Verify the Four Robot Controllers

After Gazebo has started, check Robot 1:

```bash
ros2 control list_controllers \
  -c /robot1/controller_manager
```

Repeat for the other robots:

```bash
ros2 control list_controllers \
  -c /robot2/controller_manager

ros2 control list_controllers \
  -c /robot3/controller_manager

ros2 control list_controllers \
  -c /robot4/controller_manager
```

Each robot should have:

```text
joint_state_broadcaster
joint_trajectory_controller
robotiq_gripper_controller
```

with the controllers in the `active` state.

---

# Verify Robot Actions

Check the arm trajectory actions:

```bash
ros2 action list | grep follow_joint_trajectory
```

Expected:

```text
/robot1/joint_trajectory_controller/follow_joint_trajectory
/robot2/joint_trajectory_controller/follow_joint_trajectory
/robot3/joint_trajectory_controller/follow_joint_trajectory
/robot4/joint_trajectory_controller/follow_joint_trajectory
```

Check the gripper actions:

```bash
ros2 action list | grep robotiq_gripper_controller
```

Expected:

```text
/robot1/robotiq_gripper_controller/follow_joint_trajectory
/robot2/robotiq_gripper_controller/follow_joint_trajectory
/robot3/robotiq_gripper_controller/follow_joint_trajectory
/robot4/robotiq_gripper_controller/follow_joint_trajectory
```

---

# Start MoveIt

Open another terminal attached to the same Docker container and source the environment:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

Start MoveIt:

```bash
ros2 launch robot_workcell workcell_moveit.launch.py
```

MoveIt provides a separate backend for each robot:

```text
/robot1/move_group
/robot2/move_group
/robot3/move_group
/robot4/move_group
```

---

# Verify MoveIt

Check the MoveIt nodes:

```bash
ros2 node list | grep move_group
```

Check the MoveIt actions:

```bash
ros2 action list | grep move_action
```

Expected:

```text
/robot1/move_action
/robot2/move_action
/robot3/move_action
/robot4/move_action
```

At this point the complete simulation environment is running with Gazebo, four UR10e robots, four Robotiq grippers, robot controllers, and MoveIt.

---
# Verify All Robots and Grippers

In this it uses Radian only

## Robot 1

```
ros2 action send_goal \
/robot1/joint_trajectory_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [
      robot1_shoulder_pan_joint,
      robot1_shoulder_lift_joint,
      robot1_elbow_joint,
      robot1_wrist_1_joint,
      robot1_wrist_2_joint,
      robot1_wrist_3_joint
    ],
    points: [
      {
        positions: [0.50, -1.00, 1.00, -1.00, 0.50, 0.50],
        time_from_start: {sec: 3, nanosec: 0}
      }
    ]
  }
}"
```

## Robot 2

```
ros2 action send_goal \
/robot2/joint_trajectory_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [
      robot2_shoulder_pan_joint,
      robot2_shoulder_lift_joint,
      robot2_elbow_joint,
      robot2_wrist_1_joint,
      robot2_wrist_2_joint,
      robot2_wrist_3_joint
    ],
    points: [
      {
        positions: [0.50, -1.00, 1.00, -1.00, 0.50, 0.50],
        time_from_start: {sec: 3, nanosec: 0}
      }
    ]
  }
}"
```

## Robot 3

```
ros2 action send_goal \
/robot3/joint_trajectory_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [
      robot3_shoulder_pan_joint,
      robot3_shoulder_lift_joint,
      robot3_elbow_joint,
      robot3_wrist_1_joint,
      robot3_wrist_2_joint,
      robot3_wrist_3_joint
    ],
    points: [
      {
        positions: [0.50, -1.00, 1.00, -1.00, 0.50, 0.50],
        time_from_start: {sec: 3, nanosec: 0}
      }
    ]
  }
}"
```

## Robot 4

```
ros2 action send_goal \
/robot4/joint_trajectory_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [
      robot4_shoulder_pan_joint,
      robot4_shoulder_lift_joint,
      robot4_elbow_joint,
      robot4_wrist_1_joint,
      robot4_wrist_2_joint,
      robot4_wrist_3_joint
    ],
    points: [
      {
        positions: [0.50, -1.00, 1.00, -1.00, 0.50, 0.50],
        time_from_start: {sec: 3, nanosec: 0}
      }
    ]
  }
}"
```

## Test the grippers too

### Robot 1 open

```
ros2 action send_goal \
/robot1/robotiq_gripper_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [robot1_robotiq_85_left_knuckle_joint],
    points: [
      {
        positions: [0.0],
        time_from_start: {sec: 2, nanosec: 0}
      }
    ]
  }
}"
```

### Robot 1 close

```
ros2 action send_goal \
/robot1/robotiq_gripper_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [robot1_robotiq_85_left_knuckle_joint],
    points: [
      {
        positions: [0.79],
        time_from_start: {sec: 2, nanosec: 0}
      }
    ]
  }
}"
```
For robots 2–4, substitute the prefix:

```
robot2_...
robot3_...
robot4_...
```

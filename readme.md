# Waste Sorting Robotic Workcell

A ROS 2 Jazzy and Gazebo-based robotic waste sorting simulation consisting of a custom robotic arm with an integrated gripper.

The workcell simulates a conveyor-based waste sorting system in which waste objects are transported along a conveyor and assigned to robotic stations for sorting.

## Main Components


- 1 × conveyor belt
- Plastic (Blue Bins) and metal (Gray Bins) waste sorting bins
- Robot work tables
- Custom robotic arm with gripper
- Gazebo Harmonic simulation environment
- MoveIt 2 motion planning
- `ros2_control` robot control
- Custom ROS 2 workcell launch and configuration

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

```
1 × conveyor belt
Plastic waste bins (Blue)
Metal waste bins (Gray)
Custom robotic arm
Gripper
```

## ROS 2 Packages

The workspace contains the packages required for:

- MoveIt configuration
- Conveyor belt simulation
- Custom robotic arm
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

# Workcell Launch Files

The custom workcell currently contains two launch files:

```text
robot_workcell/
└── launch/

    ├── gazebo.launch.py
    └── workcell_moveit.launch.py
````

## `gazebo.launch.py`

Starts the Gazebo simulation for the robotic arm workcell.

It handles:

- Gazebo world
- Robot State Publisher
- Robot spawning
- Gazebo/ROS `/clock` bridge
- `ros2_control`
- Joint State Broadcaster
- Arm controller
- Gripper controller

This launch file does **not** start MoveIt or the conveyor startup command.

Run:

```
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch robot_workcell gazebo.launch.py
```

---

## `workcell_moveit.launch.py`

Starts the complete robotic workcell and MoveIt 2.

This is the main launch file for the full simulation.

It directly starts:

- Gazebo workcell
- Robot State Publisher
- Robotic arm
- Gripper
- `ros2_control`
- Joint State Broadcaster
- Arm controller
- Gripper controller
- Conveyor
- MoveIt 2
- RViz (optional)

The conveyor is automatically started at 100% power.

By default, RViz is disabled.

---

# Start Complete Workcell with MoveIt

Start the complete simulation:

```
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch robot_workcell workcell_moveit.launch.py
```

To start the same system with RViz:

```
ros2 launch robot_workcell workcell_moveit.launch.py use_rviz:=true
```

The complete system is:

```
workcell_moveit.launch.py
│
├── Gazebo
│   └── waste_sorting_cell.sdf
│
├── Robot State Publisher
│
├── Robotic Arm
│
├── Gripper
│
├── ros2_control
│   ├── joint_state_broadcaster
│   ├── arm_controller
│   └── gripper_controller
│
├── Conveyor
│
├── MoveIt 2
│   └── move_group
│
└── RViz (optional)
```



# Robot Control Commands

The robot arm and gripper can also be controlled directly from the terminal without writing a separate program.

## Move Robot Arm

The arm is controlled through the MoveIt 2 `/move_action` interface.

The robot can be commanded using an **XYZ position** for the end effector (`link_4`). MoveIt performs position-only IK and motion planning to determine the required joint motion.

Example command:

```
ros2 action send_goal --feedback \
/move_action \
moveit_msgs/action/MoveGroup \
"{
  request: {
    group_name: arm,
    pipeline_id: ompl,
    num_planning_attempts: 5,
    allowed_planning_time: 10.0,
    max_velocity_scaling_factor: 1.0,
    max_acceleration_scaling_factor: 1.0,
    goal_constraints: [
      {
        position_constraints: [
          {
            header: {
              frame_id: base_link
            },
            link_name: link_4,
            constraint_region: {
              primitives: [
                {
                  type: 1,
                  dimensions: [0.02, 0.02, 0.02]
                }
              ],
              primitive_poses: [
                {
                  position: {
                    x: 0.380,
                    y: -0.003,
                    z: 0.417
                  },
                  orientation: {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                    w: 1.0
                  }
                }
              ]
            },
            weight: 1.0
          }
        ]
      }
    ]
  },
  planning_options: {
    plan_only: false,
    look_around: false,
    replan: false
  }
}"
```

This example commands MoveIt to move the `link_4` end effector to:

```
Frame: base_link

X = 0.380 m
Y = -0.003 m
Z = 0.417 m
```

The position goal uses a small 3D tolerance region:

```
0.02 m × 0.02 m × 0.02 m
```

### Motion Parameters

```
Planning group: arm
Planner: OMPL
End effector: link_4
Target frame: base_link
Target: X, Y, Z
Velocity scaling: 1.0
Acceleration scaling: 1.0
```

The four arm joints are calculated automatically by MoveIt using position-only IK. The resulting trajectory is then executed through `arm_controller`.

For a different target, change only:

```
x: ...
y: ...
z: ...
```

For example:

```
position:
  x: 0.30
  y: 0.10
  z: 0.25
```

This allows an external system such as the vision system to provide the object's **X, Y, Z position**, which can then be used as the MoveIt target.


---



## Open Gripper

The gripper is controlled through the `gripper_controller` trajectory action.

To **open the gripper**:

```
ros2 action send_goal --feedback \
/gripper_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [link_4_right_gear_joint],
    points: [
      {
        positions: [-1.0],
        time_from_start: {
          sec: 1,
          nanosec: 0
        }
      }
    ]
  }
}"
```

## Close Gripper

To **close the gripper**:

```
ros2 action send_goal --feedback \
/gripper_controller/follow_joint_trajectory \
control_msgs/action/FollowJointTrajectory \
"{
  trajectory: {
    joint_names: [link_4_right_gear_joint],
    points: [
      {
        positions: [0.0],
        time_from_start: {
          sec: 1,
          nanosec: 0
        }
      }
    ]
  }
}"
```

### Gripper Positions

```
-1.0 rad → Open
 0.0 rad → Close
```

The gripper movement duration can be changed using:

```
time_from_start:
  sec: 1
```

For example:

```
0.5 sec → faster
1.0 sec → current setting
2.0 sec → slower
```

The active gripper joint is:

```
link_4_right_gear_joint
```

The remaining gripper joints are mimic joints and follow the master joint automatically.

```

One correction from the earlier README: use **`-1.0 = open` and `0.0 = closed`
```

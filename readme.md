source /opt/ros/jazzy/setup.bash

cd ~/ros2_ws

sudo apy update

rosdep update

rosdep install \
  --from-paths src \
  --ignore-src \
  --rosdistro jazzy \
  -r -y

colcon build \
  --symlink-install \
  --parallel-workers 1

source ~/ros2_ws/install/setup.bash


ros2 launch ur_simulation_gz ur_sim_control.launch.py ur_type:=ur10e
ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur10e

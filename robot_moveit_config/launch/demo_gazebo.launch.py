import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    # ==============================================================
    # 1. Load MoveIt configuration
    # ==============================================================

    moveit_config = (
        MoveItConfigsBuilder(
            "robot_arm",
            package_name="robot_moveit_config",
        )
        .trajectory_execution(
            file_path="config/moveit_controllers.yaml"
        )
        .planning_pipelines(
            pipelines=["ompl"],
            default_planning_pipeline="ompl",
        )
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
        )
        .to_moveit_configs()
    )

    # ==============================================================
    # 2. Start Gazebo + robot + ros2_control + controllers
    # ==============================================================

    robot_workcell_share = get_package_share_directory(
        "robot_workcell"
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                robot_workcell_share,
                "launch",
                "gazebo.launch.py",
            )
        ),
        launch_arguments={
            "use_jsp": "false",
        }.items(),
    )

    # ==============================================================
    # 3. MoveIt move_group
    # ==============================================================

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {
                "use_sim_time": True,
            },
        ],
    )

    # ==============================================================
    # 4. RViz + MotionPlanning plugin
    # ==============================================================

    rviz_config = os.path.join(
        get_package_share_directory("robot_moveit_config"),
        "config",
        "moveit.rviz",
    )

    rviz = Node(
      package="rviz2",
      executable="rviz2",
      name="moveit_rviz",
      output="screen",
      arguments=[
          "-d",
          rviz_config,
      ],
      parameters=[
          moveit_config.robot_description,
          moveit_config.robot_description_semantic,
          moveit_config.robot_description_kinematics,
          moveit_config.planning_pipelines,
          moveit_config.joint_limits,
          {
              "use_sim_time": True,
          },
      ],
  )

    # ==============================================================
    # 5. Launch everything
    # ==============================================================

    return LaunchDescription(
        [
            gazebo_launch,
            move_group,
            rviz,
        ]
    )

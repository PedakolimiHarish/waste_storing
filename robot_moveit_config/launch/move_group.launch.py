#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    use_sim_time = LaunchConfiguration("use_sim_time")

    # ============================================================
    # Launch arguments
    # ============================================================

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use Gazebo simulation time",
    )

    # ============================================================
    # MoveIt configuration
    # ============================================================

    moveit_config = (
        MoveItConfigsBuilder(
            "robot_arm",
            package_name="robot_moveit_config",
        )

        .robot_description(
            file_path="config/robot_arm.urdf.xacro",
        )

        .robot_description_semantic(
            file_path="config/robot_arm.srdf",
        )

        .robot_description_kinematics(
            file_path="config/kinematics.yaml",
        )

        .joint_limits(
            file_path="config/joint_limits.yaml",
        )

        .trajectory_execution(
            file_path="config/moveit_controllers.yaml",
            moveit_manage_controllers=False,
        )

        .planning_pipelines(
            pipelines=["ompl"],
            default_planning_pipeline="ompl",
        )

        .planning_scene_monitor(
            publish_planning_scene=True,
            publish_geometry_updates=True,
            publish_state_updates=True,
            publish_transforms_updates=True,
            publish_robot_description=False,
            publish_robot_description_semantic=True,
        )

        .to_moveit_configs()
    )

    # ============================================================
    # Move Group
    # ============================================================

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.trajectory_execution,
            moveit_config.planning_scene_monitor,
            moveit_config.joint_limits,
            {
                "use_sim_time": use_sim_time,
            },
        ],
    )

    # ============================================================
    # Launch description
    # ============================================================

    return LaunchDescription([
        declare_use_sim_time,
        move_group,
    ])

#!/usr/bin/env python3

import os
import tempfile

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnShutdown
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder


# ============================================================
# Create robot-specific joint limits
# ============================================================

def create_joint_limits_file(
    robot_name,
    tf_prefix,
):

    joints = [
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint",
    ]

    max_velocity = 1.0
    max_acceleration = 3.0

    content = "joint_limits:\n"

    for joint in joints:

        joint_name = f"{tf_prefix}{joint}"

        content += f"""  {joint_name}:
    has_velocity_limits: true
    max_velocity: {max_velocity}
    has_acceleration_limits: true
    max_acceleration: {max_acceleration}
    has_jerk_limits: false
"""

    fd, path = tempfile.mkstemp(
        prefix=f"{robot_name}_joint_limits_",
        suffix=".yaml",
    )

    with os.fdopen(fd, "w") as file:
        file.write(content)

    return path


# ============================================================
# Create robot-specific MoveIt controller configuration
# ============================================================

def create_moveit_controller_file(
    robot_name,
    tf_prefix,
):

    joints = [
        f"{tf_prefix}shoulder_pan_joint",
        f"{tf_prefix}shoulder_lift_joint",
        f"{tf_prefix}elbow_joint",
        f"{tf_prefix}wrist_1_joint",
        f"{tf_prefix}wrist_2_joint",
        f"{tf_prefix}wrist_3_joint",
    ]

    content = """\
moveit_controller_manager: moveit_simple_controller_manager/MoveItSimpleControllerManager

trajectory_execution:
  allowed_execution_duration_scaling: 1.2
  allowed_goal_duration_margin: 0.5
  allowed_start_tolerance: 0.01
  execution_duration_monitoring: false

moveit_simple_controller_manager:
  controller_names:
    - joint_trajectory_controller

  joint_trajectory_controller:
    action_ns: follow_joint_trajectory
    type: FollowJointTrajectory
    default: true
    joints:
"""

    for joint in joints:
        content += f"      - {joint}\n"

    fd, path = tempfile.mkstemp(
        prefix=f"{robot_name}_moveit_controllers_",
        suffix=".yaml",
    )

    with os.fdopen(fd, "w") as file:
        file.write(content)

    return path


# ============================================================
# Cleanup
# ============================================================

def cleanup_temp_files(paths):

    for path in paths:

        try:

            if path and os.path.exists(path):

                os.remove(path)

                print(
                    f"[robot_workcell] Removed temporary file: {path}"
                )

        except OSError as exc:

            print(
                f"[robot_workcell] Could not remove "
                f"{path}: {exc}"
            )


# ============================================================
# Launch setup
# ============================================================

def launch_setup(
    context,
    *args,
    **kwargs,
):

    robot_name = LaunchConfiguration(
        "robot_name"
    ).perform(context)

    tf_prefix = LaunchConfiguration(
        "tf_prefix"
    ).perform(context)

    ur_type = LaunchConfiguration(
        "ur_type"
    ).perform(context)

    description_file = LaunchConfiguration(
        "description_file"
    ).perform(context)

    srdf_file = LaunchConfiguration(
        "srdf_file"
    ).perform(context)

    # --------------------------------------------------------
    # Generate robot-specific files
    # --------------------------------------------------------

    joint_limits_file = create_joint_limits_file(
        robot_name,
        tf_prefix,
    )

    moveit_controller_file = create_moveit_controller_file(
        robot_name,
        tf_prefix,
    )

    print(
        f"[robot_workcell] Generated joint limits: "
        f"{joint_limits_file}"
    )

    print(
        f"[robot_workcell] Generated MoveIt controllers: "
        f"{moveit_controller_file}"
    )

    temp_files = [
        joint_limits_file,
        moveit_controller_file,
    ]

    cleanup_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                OpaqueFunction(
                    function=lambda context:
                    cleanup_temp_files(temp_files)
                )
            ]
        )
    )

    # --------------------------------------------------------
    # URDF mappings
    # --------------------------------------------------------

    urdf_mappings = {
        "name": robot_name,
        "ur_type": ur_type,
        "tf_prefix": tf_prefix,
        "safety_limits": "true",
        "safety_pos_margin": "0.15",
        "safety_k_position": "20",
    }

    # --------------------------------------------------------
    # SRDF mappings
    # --------------------------------------------------------

    srdf_mappings = {
        "name": robot_name,
        "prefix": tf_prefix,
    }

    # --------------------------------------------------------
    # MoveIt configuration
    # --------------------------------------------------------

    moveit_config = (
        MoveItConfigsBuilder(
            "ur",
            package_name="ur_moveit_config",
        )

        .robot_description(
            file_path=description_file,
            mappings=urdf_mappings,
        )

        .robot_description_semantic(
            file_path=srdf_file,
            mappings=srdf_mappings,
        )

        .robot_description_kinematics(
            file_path="config/kinematics.yaml",
        )

        # IMPORTANT:
        # Use our generated robot-specific limits.
        .joint_limits(
            file_path=joint_limits_file,
        )

        .planning_pipelines(
            pipelines=[
                "ompl",
                "pilz_industrial_motion_planner",
            ],
        )

        .pilz_cartesian_limits(
            file_path="config/pilz_cartesian_limits.yaml",
        )

        .trajectory_execution(
            file_path=moveit_controller_file,
            moveit_manage_controllers=False,
        )

        .planning_scene_monitor(
            publish_planning_scene=True,
            publish_geometry_updates=True,
            publish_state_updates=True,
            publish_transforms_updates=True,
            publish_robot_description=False,
            publish_robot_description_semantic=False,
        )

        .to_moveit_configs()
    )

    # --------------------------------------------------------
    # MoveGroup
    # --------------------------------------------------------

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",

        namespace=robot_name,
        name="move_group",

        output="screen",

        parameters=[
            moveit_config.to_dict(),

            {
                "use_sim_time": True,
                "publish_robot_description_semantic": True,
            },
        ],
    )

    return [
        move_group,
        cleanup_handler,
    ]


# ============================================================
# Launch description
# ============================================================

def generate_launch_description():

    workcell_share = get_package_share_directory(
        "robot_workcell"
    )

    ur_simulation_share = get_package_share_directory(
        "ur_simulation_gz"
    )

    description_file = os.path.join(
        ur_simulation_share,
        "urdf",
        "ur_gz.urdf.xacro",
    )

    srdf_file = os.path.join(
        workcell_share,
        "config",
        "robot_workcell.srdf.xacro",
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            "robot_name",
            default_value="robot1",
        ),

        DeclareLaunchArgument(
            "tf_prefix",
            default_value="robot1_",
        ),

        DeclareLaunchArgument(
            "ur_type",
            default_value="ur10e",
        ),

        DeclareLaunchArgument(
            "description_file",
            default_value=description_file,
        ),

        DeclareLaunchArgument(
            "srdf_file",
            default_value=srdf_file,
        ),

        OpaqueFunction(
            function=launch_setup,
        ),
    ])

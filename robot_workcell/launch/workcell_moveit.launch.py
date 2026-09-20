#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution

from moveit_configs_utils import MoveItConfigsBuilder


def create_conveyor_start_command():

    script = r"""
        echo "[workcell] Waiting for conveyor control service..."

        until ros2 service list 2>/dev/null | grep -q "^/CONVEYORPOWER$"; do
            sleep 1
        done

        echo "[workcell] Conveyor service READY"
        echo "[workcell] Starting conveyor at 100% power..."

        ros2 service call \
            /CONVEYORPOWER \
            conveyorbelt_msgs/srv/ConveyorBeltControl \
            "{power: 100.0}"

        echo "[workcell] Conveyor START command sent"
    """

    return ExecuteProcess(
        cmd=["bash", "-c", script],
        output="screen",
    )


def generate_launch_description():

    # ==========================================================
    # Package names
    # ==========================================================

    workcell_package = "robot_workcell"
    description_package = "robot_arm_description"

    # ==========================================================
    # Package paths
    # ==========================================================

    workcell_share = get_package_share_directory(
        workcell_package
    )

    description_share = get_package_share_directory(
        description_package
    )

    conveyor_share = FindPackageShare(
        package="conveyorbelt_gz"
    ).find("conveyorbelt_gz")

    ros_gz_sim_share = FindPackageShare(
        package="ros_gz_sim"
    ).find("ros_gz_sim")

    robot_moveit_share = get_package_share_directory(
        "robot_moveit_config"
    )

    # ==========================================================
    # Paths
    # ==========================================================

    world_file = os.path.join(
        workcell_share,
        "worlds",
        "waste_sorting_cell.sdf",
    )

    gazebo_models_path = os.path.join(
        workcell_share,
        "models",
    )

    conveyor_models_path = os.path.join(
        conveyor_share,
        "models",
    )

    description_share_parent = os.path.dirname(
        description_share
    )

    robot_state_publisher_launch = os.path.join(
        description_share,
        "launch",
        "robot_state_publisher.launch.py",
    )

    moveit_rviz_config = os.path.join(
        robot_moveit_share,
        "config",
        "moveit.rviz",
    )

    # ==========================================================
    # Launch arguments
    # ==========================================================

    use_rviz = LaunchConfiguration(
        "use_rviz"
    )

    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz",
        default_value="false",
        description="Launch RViz",
    )

    # ==========================================================
    # MoveIt configuration
    # ==========================================================

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

    # ==========================================================
    # Robot State Publisher
    # ==========================================================

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            robot_state_publisher_launch
        ),
        launch_arguments={
            "use_jsp": "false",
            "jsp_gui": "false",
            "use_rviz": "false",
            "use_sim_time": "true",
        }.items(),
    )

    # ==========================================================
    # Gazebo resource path
    # ==========================================================

    set_gz_resource_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.pathsep.join([
            gazebo_models_path,
            conveyor_models_path,
            description_share_parent,
        ]),
    )

    # ==========================================================
    # Start Gazebo
    # ==========================================================

    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ros_gz_sim_share,
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={
            "gz_args": f"-r -v 4 {world_file}",
        }.items(),
    )

    # ==========================================================
    # Gazebo / ROS clock bridge
    # ==========================================================

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
        ],
        output="screen",
    )

    # ==========================================================
    # Spawn robot
    # ==========================================================

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "/robot_description",

            "-name",
            "robot_arm",

            "-allow_renaming",
            "true",

            "-x",
            "0.0",

            "-y",
            "0.4",

            "-z",
            "0.7",

            "-R",
            "0.0",

            "-P",
            "0.0",

            "-Y",
            "-1.5708",
        ],
    )

    # ==========================================================
    # Joint State Broadcaster
    # ==========================================================

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    # ==========================================================
    # Arm Controller
    # ==========================================================

    arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    # ==========================================================
    # Gripper Controller
    # ==========================================================

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    # ==========================================================
    # Controller startup sequence
    #
    # joint_state_broadcaster
    #          ↓
    # arm_controller
    #          ↓
    # gripper_controller
    # ==========================================================

    start_joint_state_broadcaster = TimerAction(
        period=2.0,
        actions=[
            joint_state_broadcaster
        ],
    )

    start_arm_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[
                arm_controller
            ],
        )
    )

    start_gripper_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller,
            on_exit=[
                gripper_controller
            ],
        )
    )

    # ==========================================================
    # MoveIt move_group
    # ==========================================================

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

    # ==========================================================
    # RViz
    # ==========================================================

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="moveit_rviz",
        output="screen",
        arguments=[
            "-d",
            moveit_rviz_config,
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
        condition=IfCondition(use_rviz),
    )

    # ==========================================================
    # Conveyor startup
    # ==========================================================

    conveyor_start = create_conveyor_start_command()

    # ==========================================================
    # Launch
    # ==========================================================

    return LaunchDescription([

        # Arguments
        declare_use_rviz,

        # Environment
        set_gz_resource_path,

        # Robot State Publisher
        robot_state_publisher,

        # Gazebo
        start_gazebo,

        # Clock
        clock_bridge,

        # Robot
        spawn_robot,

        # Controllers
        start_joint_state_broadcaster,
        start_arm_controller,
        start_gripper_controller,

        # Conveyor
        conveyor_start,

        # MoveIt
        move_group,

        # RViz
        rviz,
    ])

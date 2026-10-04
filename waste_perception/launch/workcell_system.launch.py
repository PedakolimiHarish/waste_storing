#!/usr/bin/env python3

import os

from ament_index_python.packages import (
    get_package_share_directory,
)

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)

from launch.conditions import IfCondition

from launch.event_handlers import OnProcessExit

from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
)

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    # ==========================================================
    # Package names
    # ==========================================================

    workcell_package = "robot_workcell"

    description_package = "robot_arm_description"

    moveit_package = "robot_moveit_config"


    # ==========================================================
    # Package paths
    # ==========================================================

    workcell_share = get_package_share_directory(
        workcell_package
    )

    description_share = get_package_share_directory(
        description_package
    )

    moveit_share = get_package_share_directory(
        moveit_package
    )


    ros_gz_sim_share = get_package_share_directory(
        "ros_gz_sim"
    )


    # ==========================================================
    # Paths
    # ==========================================================

    world_file = os.path.join(
        workcell_share,
        "worlds",
        "waste_sorting_cell.sdf",
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
        moveit_share,
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
            package_name=moveit_package,
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

        name="GZ_SIM_RESOURCE_PATH",

        value=os.pathsep.join([
            os.path.join(
                workcell_share,
                "models",
            ),

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
    # Clock bridge
    # ==========================================================

    clock_bridge = Node(

        package="ros_gz_bridge",

        executable="parameter_bridge",

        name="clock_bridge",

        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
        ],

        output="screen",
    )


    # ==========================================================
    # Camera image bridge
    # ==========================================================

    camera_image_bridge = Node(

        package="ros_gz_image",

        executable="image_bridge",

        name="camera_image_bridge",

        arguments=[
            "/sorting_camera/image"
        ],

        output="screen",
    )


    # ==========================================================
    # Camera info bridge
    # ==========================================================

    camera_info_bridge = Node(

        package="ros_gz_bridge",

        executable="parameter_bridge",

        name="camera_info_bridge",

        arguments=[
            "/sorting_camera/camera_info"
            "@sensor_msgs/msg/CameraInfo"
            "[gz.msgs.CameraInfo"
        ],

        output="screen",
    )

    # ==========================================================
    # Vision Processor
    # ==========================================================

    vision_processor = Node(
        package="waste_perception",
        executable="vision_processor",
        name="vision_processor",
        output="screen",
    )


    # ==========================================================
    # Task Manager
    # ==========================================================

    task_manager = Node(
        package="waste_perception",
        executable="task_manager",
        name="task_manager",
        output="screen",
    )

    # ==========================================================
    # Gazebo object spawn service bridge
    # ==========================================================

    spawn_service_bridge = Node(

        package="ros_gz_bridge",

        executable="parameter_bridge",

        name="spawn_service_bridge",

        arguments=[
            "/world/waste_sorting_cell/create"
            "@ros_gz_interfaces/srv/SpawnEntity"
        ],

        output="screen",
    )

    # ==========================================================
    # Gazebo object pose bridge
    # ==========================================================

    set_pose_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="set_pose_bridge",
        arguments=[
            "/world/waste_sorting_cell/set_pose@ros_gz_interfaces/srv/SetEntityPose"
        ],
        output="screen",
    )

    # ==========================================================
    # Gazebo object remove service bridge
    # ==========================================================

    remove_service_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="remove_service_bridge",
        arguments=[
            "/world/waste_sorting_cell/remove"
            "@ros_gz_interfaces/srv/DeleteEntity"
        ],
        output="screen",
    )


    # ==========================================================
    # Spawn robot
    # ==========================================================

    spawn_robot = Node(

        package="ros_gz_sim",

        executable="create",

        name="spawn_robot",

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
            "0.5",

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

    spawn_robot_delayed = TimerAction(
        period=3.0,
        actions=[spawn_robot],
    )

    # ==========================================================
    # Joint State Broadcaster
    # ==========================================================

    joint_state_broadcaster = Node(

        package="controller_manager",

        executable="spawner",

        name="joint_state_broadcaster_spawner",

        output="screen",

        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )


    # ==========================================================
    # Arm Controller
    # ==========================================================

    arm_controller = Node(

        package="controller_manager",

        executable="spawner",

        name="arm_controller_spawner",

        output="screen",

        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )


    # ==========================================================
    # Gripper Controller
    # ==========================================================

    gripper_controller = Node(

        package="controller_manager",

        executable="spawner",

        name="gripper_controller_spawner",

        output="screen",

        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
        ],
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
        name="move_group",
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

        condition=IfCondition(
            use_rviz
        ),
    )


    # ==========================================================
    # Launch
    # ==========================================================

    return LaunchDescription([

        # ------------------------------------------------------
        # Arguments
        # ------------------------------------------------------

        declare_use_rviz,


        # ------------------------------------------------------
        # Environment
        # ------------------------------------------------------

        set_gz_resource_path,


        # ------------------------------------------------------
        # Robot State Publisher
        # ------------------------------------------------------

        robot_state_publisher,


        # ------------------------------------------------------
        # Gazebo
        # ------------------------------------------------------

        start_gazebo,


        # ------------------------------------------------------
        # ROS <-> Gazebo bridges
        # ------------------------------------------------------

        clock_bridge,

        camera_image_bridge,

        camera_info_bridge,

        spawn_service_bridge,

        set_pose_bridge,

        remove_service_bridge,


        # ------------------------------------------------------
        # Robot
        # ------------------------------------------------------

        spawn_robot_delayed,


        # ------------------------------------------------------
        # Controllers
        # ------------------------------------------------------

        start_joint_state_broadcaster,

        start_arm_controller,

        start_gripper_controller,


        # ------------------------------------------------------
        # MoveIt
        # ------------------------------------------------------

        move_group,

        # ------------------------------------------------------
        # Perception and task execution
        # ------------------------------------------------------

        vision_processor,
        task_manager,

        # ------------------------------------------------------
        # RViz
        # ------------------------------------------------------

        rviz,
    ])

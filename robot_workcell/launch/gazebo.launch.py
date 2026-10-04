#!/usr/bin/env python3

import os

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
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():

    # ============================================================
    # Package names
    # ============================================================

    package_name_gazebo = 'robot_workcell'
    package_name_description = 'robot_arm_description'

    gazebo_models_dir = 'models'
    gazebo_worlds_dir = 'worlds'
    default_world_file = 'empty.world'

    # ============================================================
    # Package paths
    # ============================================================

    pkg_ros_gz_sim = FindPackageShare(
        package='ros_gz_sim'
    ).find('ros_gz_sim')

    pkg_share_gazebo = FindPackageShare(
        package=package_name_gazebo
    ).find(package_name_gazebo)

    pkg_share_description = FindPackageShare(
        package=package_name_description
    ).find(package_name_description)

    description_share_parent = os.path.dirname(pkg_share_description)

    gazebo_models_path = os.path.join(
        pkg_share_gazebo,
        gazebo_models_dir
    )

    # ============================================================
    # Launch configurations
    # ============================================================

    robot_name = LaunchConfiguration('robot_name')

    jsp_gui = LaunchConfiguration('jsp_gui')
    use_rviz = LaunchConfiguration('use_rviz')
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_sim_time = LaunchConfiguration('use_sim_time')

    world_file = LaunchConfiguration('world_file')

    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')

    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    # ============================================================
    # World path
    # ============================================================

    world_path = PathJoinSubstitution([
        pkg_share_gazebo,
        gazebo_worlds_dir,
        world_file
    ])

    # ============================================================
    # Launch arguments
    # ============================================================

    declare_robot_name = DeclareLaunchArgument(
        'robot_name',
        default_value='robot_arm',
        description='Name of the robot entity in Gazebo'
    )

    declare_jsp_gui = DeclareLaunchArgument(
        'jsp_gui',
        default_value='false',
        description='Launch joint_state_publisher_gui'
    )

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz'
    )

    declare_use_gazebo = DeclareLaunchArgument(
        'use_gazebo',
        default_value='true',
        description='Use Gazebo simulation'
    )

    declare_use_robot_state_pub = DeclareLaunchArgument(
        'use_robot_state_pub',
        default_value='true',
        description='Launch robot_state_publisher'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock'
    )

    declare_world = DeclareLaunchArgument(
        'world_file',
        default_value=default_world_file,
        description='Gazebo world file'
    )

    declare_x = DeclareLaunchArgument(
        'x',
        default_value='0.0',
        description='Robot spawn X position'
    )

    declare_y = DeclareLaunchArgument(
        'y',
        default_value='0.0',
        description='Robot spawn Y position'
    )

    declare_z = DeclareLaunchArgument(
        'z',
        default_value='0.05',
        description='Robot spawn Z position'
    )

    declare_roll = DeclareLaunchArgument(
        'roll',
        default_value='0.0',
        description='Robot spawn roll'
    )

    declare_pitch = DeclareLaunchArgument(
        'pitch',
        default_value='0.0',
        description='Robot spawn pitch'
    )

    declare_yaw = DeclareLaunchArgument(
        'yaw',
        default_value='0.0',
        description='Robot spawn yaw'
    )

    # ============================================================
    # Robot State Publisher
    # ============================================================

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_share_description,
                'launch',
                'robot_state_publisher.launch.py'
            )
        ),
        launch_arguments={
            'use_jsp': 'false',
            'jsp_gui': 'false',
            'use_rviz': use_rviz,
            'use_sim_time': use_sim_time
        }.items(),
        condition=IfCondition(use_robot_state_pub)
    )

    # ============================================================
    # Gazebo resource path
    # ============================================================

    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.pathsep.join([
            gazebo_models_path,
            description_share_parent,
        ])
    )

    # ============================================================
    # Start Gazebo
    # ============================================================

    start_gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_ros_gz_sim,
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments=[
            (
                'gz_args',
                [
                    '-r -v 4 ',
                    world_path
                ]
            )
        ]
    )

    # ============================================================
    # Start Gazebo clock bridge
    # ============================================================

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )

    # ============================================================
    # Spawn robot into Gazebo
    # ============================================================

    spawn_robot_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/robot_description',

            '-name', robot_name,
            '-allow_renaming', 'true',

            '-x', x,
            '-y', y,
            '-z', z,

            '-R', roll,
            '-P', pitch,
            '-Y', yaw
        ]
    )

    # ============================================================
    # Joint State Broadcaster
    #
    # This publishes joint states from ros2_control.
    #
    # It must be started before the arm/gripper controllers.
    # ============================================================

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager'
        ],
        output='screen'
    )

    # ============================================================
    # Arm Controller
    #
    # Your current arm has 4 DOF:
    #
    # base_link_link_1
    # link_1_link_2
    # link_2_link_3
    # link_3_link_4
    # ============================================================

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_controller',
            '--controller-manager',
            '/controller_manager'
        ],
        output='screen'
    )

    # ============================================================
    # Gripper Controller
    #
    # Master joint:
    #
    # link_4_right_gear_joint
    #
    # The other 5 joints are mimic joints.
    # ============================================================

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'gripper_controller',
            '--controller-manager',
            '/controller_manager'
        ],
        output='screen'
    )

    # ============================================================
    # Controller startup sequence
    #
    # Gazebo -> robot -> controller_manager
    #
    # Wait a little before starting the first spawner.
    # The spawner itself waits for controller_manager.
    # ============================================================

    start_joint_state_broadcaster = TimerAction(
        period=2.0,
        actions=[
            joint_state_broadcaster_spawner
        ]
    )

    # Start arm controller only after joint_state_broadcaster exits
    start_arm_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[
                arm_controller_spawner
            ]
        )
    )

    # Start gripper controller only after arm controller exits
    start_gripper_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[
                gripper_controller_spawner
            ]
        )
    )

    # ============================================================
    # Launch Description
    # ============================================================

    ld = LaunchDescription()

    # -----------------------------
    # Arguments
    # -----------------------------

    ld.add_action(declare_robot_name)

    ld.add_action(declare_jsp_gui)
    ld.add_action(declare_use_rviz)
    ld.add_action(declare_use_gazebo)
    ld.add_action(declare_use_robot_state_pub)
    ld.add_action(declare_use_sim_time)

    ld.add_action(declare_world)

    ld.add_action(declare_x)
    ld.add_action(declare_y)
    ld.add_action(declare_z)

    ld.add_action(declare_roll)
    ld.add_action(declare_pitch)
    ld.add_action(declare_yaw)

    # -----------------------------
    # Environment
    # -----------------------------

    ld.add_action(set_env_vars_resources)

    # -----------------------------
    # Robot state publisher
    # -----------------------------

    ld.add_action(robot_state_publisher_cmd)

    # -----------------------------
    # Gazebo
    # -----------------------------

    ld.add_action(start_gazebo_cmd)

    # -----------------------------
    # Spawn robot
    # -----------------------------

    ld.add_action(spawn_robot_cmd)

    # -----------------------------
    # Clock bridge
    # -----------------------------

    ld.add_action(clock_bridge)

    # -----------------------------
    # Controllers
    # -----------------------------

    ld.add_action(start_joint_state_broadcaster)

    ld.add_action(start_arm_controller)

    ld.add_action(start_gripper_controller)

    return ld

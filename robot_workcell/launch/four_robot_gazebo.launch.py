from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue, ParameterFile
from launch_ros.substitutions import FindPackageShare


def make_robot(
    name,
    tf_prefix,
    x,
    y,
    controllers_file,
    description_file,
):
    robot_description = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            description_file,
            " ",
            "name:=",
            name,
            " ",
            "ur_type:=ur10e",
            " ",
            "tf_prefix:=",
            tf_prefix,
            " ",
            "simulation_controllers:=",
            controllers_file,
            " ",
            "ros_namespace:=",
            name,
        ]
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=name,
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
                "robot_description": ParameterValue(
                    robot_description,
                    value_type=str,
                ),
            }
        ],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-string",
            robot_description,
            "-name",
            name,
            "-x",
            str(x),
            "-y",
            str(y),
            "-z",
            "0.0",
            "-allow_renaming",
            "false",
        ],
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        namespace=name,
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            f"/{name}/controller_manager",
        ],
        output="screen",
    )

    joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        namespace=name,
        arguments=[
            "joint_trajectory_controller",
            "--controller-manager",
            f"/{name}/controller_manager",
            "--param-file",
            controllers_file,
        ],
        output="screen",
    )

    return [
        robot_state_publisher,
        spawn_robot,
        joint_state_broadcaster,
        joint_trajectory_controller,
    ]


def generate_launch_description():

    robot_workcell_share = FindPackageShare("robot_workcell")

    ur_description_file = PathJoinSubstitution(
        [
            robot_workcell_share,
            "urdf",
            "ur10e_workcell.xacro",
        ]
    )

    controllers_file = PathJoinSubstitution(
        [
            robot_workcell_share,
            "config",
            "controllers.yaml",
        ]
    )

    world_file = PathJoinSubstitution(
        [
            robot_workcell_share,
            "worlds",
            "four_robot_cell.sdf",
        ]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                FindPackageShare("ros_gz_sim"),
                "/launch/gz_sim.launch.py",
            ]
        ),
        launch_arguments={
            "gz_args": [
                "-r -v 4 ",
                world_file,
            ],
        }.items(),
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    robots = []

    robots += make_robot(
        "robot1",
        "robot1_",
        -1.0,
        1.35,
        controllers_file,
        ur_description_file,
    )

    robots += make_robot(
        "robot2",
        "robot2_",
        1.0,
        1.35,
        controllers_file,
        ur_description_file,
    )

    robots += make_robot(
        "robot3",
        "robot3_",
        -1.0,
        -1.35,
        controllers_file,
        ur_description_file,
    )

    robots += make_robot(
        "robot4",
        "robot4_",
        1.0,
        -1.35,
        controllers_file,
        ur_description_file,
    )

    return LaunchDescription(
        [
            gazebo,
            clock_bridge,
            *robots,
        ]
    )

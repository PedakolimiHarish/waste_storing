#!/usr/bin/env python3

import time

import rclpy
from rclpy.action import ActionClient

from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

from moveit import MoveItPy
from moveit.planning import PlanRequestParameters
from moveit.core import RobotState

from moveit_configs_utils import MoveItConfigsBuilder


# ============================================================
# ARM JOINTS
# ============================================================

ARM_JOINTS = [
    "base_link_link_1",
    "link_1_link_2",
    "link_2_link_3",
    "link_3_link_4",
]


# ============================================================
# TEST POSITIONS
# ============================================================
#
# [joint1, joint2, joint3, joint4]
#
# Change these values for your robot.
#

POINT_1 = [
    0.0,
    -0.8,
    1.2,
    -0.5,
]

POINT_2 = [
    0.5,
    -0.6,
    1.0,
    -0.3,
]


# ============================================================
# SPEED
# ============================================================

ARM_VELOCITY = 0.3
ARM_ACCELERATION = 0.3

GRIPPER_OPEN = 0.0
GRIPPER_CLOSE = -0.4

GRIPPER_OPEN_TIME = 1.0
GRIPPER_CLOSE_TIME = 1.0

GRIPPER_JOINT = "link_4_right_gear_joint"


# ============================================================
# MOVEIT CONFIG
# ============================================================

def create_moveit_config():

    config = (
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
        .to_dict()
    )

    # MoveItPy / MoveItCpp expects this format
    config["planning_pipelines"] = {
        "pipeline_names": ["ompl"]
    }

    return config


# ============================================================
# MOVE ARM
# ============================================================

def move_arm(robot, arm, logger, joint_values):

    logger.info(
        f"Moving arm to: {joint_values}"
    )

    # Current state = starting state
    arm.set_start_state_to_current_state()

    # Create target robot state
    robot_state = RobotState(
        robot.get_robot_model()
    )

    robot_state.joint_positions = dict(
        zip(ARM_JOINTS, joint_values)
    )

    # Set joint-space goal
    arm.set_goal_state(
        robot_state=robot_state
    )

    # Planning parameters
    params = PlanRequestParameters(
        robot,
        "",
    )

    params.planning_pipeline = "ompl"
    params.planner_id = ""

    params.planning_attempts = 1
    params.planning_time = 3.0

    params.max_velocity_scaling_factor = (
        ARM_VELOCITY
    )

    params.max_acceleration_scaling_factor = (
        ARM_ACCELERATION
    )

    logger.info("Planning...")

    plan = arm.plan(
        single_plan_parameters=params
    )

    if not plan:

        logger.error(
            "Arm planning failed."
        )

        return False

    logger.info(
        "Planning successful."
    )

    logger.info(
        "Executing..."
    )

    result = robot.execute(
        plan.trajectory,
        controllers=["arm_controller"],
    )

    logger.info(
        f"Execution result: {result}"
    )

    return True


# ============================================================
# MOVE GRIPPER
# ============================================================

def move_gripper(
    node,
    client,
    logger,
    position,
    duration,
):

    logger.info(
        f"Moving gripper to {position:.3f} rad"
    )

    if not client.wait_for_server(
        timeout_sec=5.0
    ):

        logger.error(
            "Gripper action server not available."
        )

        return False

    goal = FollowJointTrajectory.Goal()

    goal.trajectory.joint_names = [
        GRIPPER_JOINT
    ]

    point = JointTrajectoryPoint()

    point.positions = [
        position
    ]

    sec = int(duration)

    nanosec = int(
        (duration - sec) * 1e9
    )

    point.time_from_start.sec = sec
    point.time_from_start.nanosec = nanosec

    goal.trajectory.points = [
        point
    ]

    future = client.send_goal_async(
        goal
    )

    rclpy.spin_until_future_complete(
        node,
        future,
    )

    goal_handle = future.result()

    if goal_handle is None:
        logger.error(
            "No response from gripper."
        )
        return False

    if not goal_handle.accepted:
        logger.error(
            "Gripper goal rejected."
        )
        return False

    result_future = (
        goal_handle.get_result_async()
    )

    rclpy.spin_until_future_complete(
        node,
        result_future,
    )

    result = result_future.result().result

    if result.error_code != 0:

        logger.error(
            f"Gripper error: "
            f"{result.error_string}"
        )

        return False

    logger.info(
        "Gripper movement complete."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    rclpy.init()

    logger = rclpy.logging.get_logger(
        "test_pick_place"
    )

    logger.info(
        "========================================"
    )
    logger.info(
        "       SIMPLE PICK & PLACE TEST"
    )
    logger.info(
        "========================================"
    )

    # --------------------------------------------------------
    # Normal ROS node for gripper action
    # --------------------------------------------------------

    node = rclpy.create_node(
        "test_pick_place"
    )

    # --------------------------------------------------------
    # MoveItPy
    # --------------------------------------------------------

    config = create_moveit_config()

    robot = MoveItPy(
        node_name="pick_place_demo",
        config_dict=config,
    )

    arm = robot.get_planning_component(
        "arm"
    )

    # --------------------------------------------------------
    # Gripper action client
    # --------------------------------------------------------

    gripper_client = ActionClient(
        node,
        FollowJointTrajectory,
        "/gripper_controller/follow_joint_trajectory",
    )

    time.sleep(2.0)

    # ========================================================
    # STEP 1
    # ========================================================

    logger.info(
        "STEP 1: Move to POINT 1"
    )

    if not move_arm(
        robot,
        arm,
        logger,
        POINT_1,
    ):
        return

    time.sleep(0.5)

    # ========================================================
    # STEP 2
    # ========================================================

    logger.info(
        "STEP 2: OPEN GRIPPER"
    )

    if not move_gripper(
        node,
        gripper_client,
        logger,
        GRIPPER_OPEN,
        GRIPPER_OPEN_TIME,
    ):
        return

    time.sleep(0.5)

    # ========================================================
    # STEP 3
    # ========================================================

    logger.info(
        "STEP 3: CLOSE GRIPPER"
    )

    if not move_gripper(
        node,
        gripper_client,
        logger,
        GRIPPER_CLOSE,
        GRIPPER_CLOSE_TIME,
    ):
        return

    time.sleep(0.5)

    # ========================================================
    # STEP 4
    # ========================================================

    logger.info(
        "STEP 4: Move to POINT 2"
    )

    if not move_arm(
        robot,
        arm,
        logger,
        POINT_2,
    ):
        return

    time.sleep(0.5)

    # ========================================================
    # STEP 5
    # ========================================================

    logger.info(
        "STEP 5: OPEN GRIPPER"
    )

    move_gripper(
        node,
        gripper_client,
        logger,
        GRIPPER_OPEN,
        GRIPPER_OPEN_TIME,
    )

    # ========================================================
    # DONE
    # ========================================================

    logger.info(
        "========================================"
    )
    logger.info(
        "           TEST COMPLETE"
    )
    logger.info(
        "========================================"
    )

    robot.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

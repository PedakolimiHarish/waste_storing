#!/usr/bin/env python3

import sys
import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
from shape_msgs.msg import SolidPrimitive
from rclpy.action import ActionClient


class MoveItRobot1Test(Node):

    def __init__(self):
        super().__init__("test_moveit_robot1")

        self.client = ActionClient(
            self,
            MoveGroup,
            "/robot1/move_group",
        )

    def run(self):
        self.get_logger().info(
            "Waiting for /robot1/move_group..."
        )

        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error(
                "MoveIt move_group action server not available."
            )
            return False

        self.get_logger().info(
            "Connected to /robot1/move_group"
        )

        goal = MoveGroup.Goal()

        goal.request.group_name = "ur_manipulator"

        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2

        goal.request.start_state.is_diff = True

        # ------------------------------------------------------
        # Target pose for Robot 1
        # ------------------------------------------------------

        position_constraint = PositionConstraint()

        position_constraint.header.frame_id = (
            "robot1_base_link"
        )

        position_constraint.link_name = (
            "robot1_tool0"
        )

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [
            0.02,
            0.02,
            0.02,
        ]

        position_constraint.constraint_region.primitives.append(
            primitive
        )

        target = Pose()

        target.position.x = 0.30
        target.position.y = 0.00
        target.position.z = 0.40

        target.orientation.x = 0.0
        target.orientation.y = 0.7071
        target.orientation.z = 0.0
        target.orientation.w = 0.7071

        position_constraint.constraint_region.primitive_poses.append(
            target
        )

        position_constraint.weight = 1.0

        orientation_constraint = OrientationConstraint()

        orientation_constraint.header.frame_id = (
            "robot1_base_link"
        )

        orientation_constraint.link_name = (
            "robot1_tool0"
        )

        orientation_constraint.orientation = (
            target.orientation
        )

        orientation_constraint.absolute_x_axis_tolerance = 0.1
        orientation_constraint.absolute_y_axis_tolerance = 0.1
        orientation_constraint.absolute_z_axis_tolerance = 0.1
        orientation_constraint.weight = 1.0

        constraints = Constraints()

        constraints.position_constraints.append(
            position_constraint
        )

        constraints.orientation_constraints.append(
            orientation_constraint
        )

        goal.request.goal_constraints.append(
            constraints
        )

        # ------------------------------------------------------
        # Plan only first
        # ------------------------------------------------------

        goal.request.planner_id = ""

        self.get_logger().info(
            "Requesting MoveIt plan..."
        )

        send_future = self.client.send_goal_async(goal)

        rclpy.spin_until_future_complete(
            self,
            send_future,
        )

        goal_handle = send_future.result()

        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error(
                "MoveIt rejected the planning request."
            )
            return False

        self.get_logger().info(
            "MoveIt planning goal accepted."
        )

        result_future = goal_handle.get_result_async()

        rclpy.spin_until_future_complete(
            self,
            result_future,
        )

        result = result_future.result().result

        self.get_logger().info(
            f"MoveIt error code: "
            f"{result.error_code.val}"
        )

        # MoveIt SUCCESS == 1
        if result.error_code.val != 1:
            self.get_logger().error(
                "MoveIt failed to produce a valid plan."
            )
            return False

        self.get_logger().info(
            "Plan generated successfully."
        )

        trajectory = result.planned_trajectory.joint_trajectory

        self.get_logger().info(
            f"Trajectory contains "
            f"{len(trajectory.points)} points."
        )

        # ------------------------------------------------------
        # Execute the trajectory
        # ------------------------------------------------------

        execute_goal = MoveGroup.Goal()

        execute_goal.request = goal.request

        # Tell MoveGroup to execute
        execute_goal.planning_options.plan_only = False
        execute_goal.planning_options.replan = False
        execute_goal.planning_options.replan_attempts = 0

        self.get_logger().info(
            "Requesting MoveIt execution..."
        )

        send_future = self.client.send_goal_async(
            execute_goal
        )

        rclpy.spin_until_future_complete(
            self,
            send_future,
        )

        execute_handle = send_future.result()

        if not execute_handle or not execute_handle.accepted:
            self.get_logger().error(
                "MoveIt rejected execution request."
            )
            return False

        self.get_logger().info(
            "Execution request accepted."
        )

        result_future = execute_handle.get_result_async()

        rclpy.spin_until_future_complete(
            self,
            result_future,
        )

        execution_result = result_future.result().result

        self.get_logger().info(
            f"Execution error code: "
            f"{execution_result.error_code.val}"
        )

        return execution_result.error_code.val == 1


def main(args=None):

    rclpy.init(args=args)

    node = MoveItRobot1Test()

    try:
        success = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

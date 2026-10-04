#!/usr/bin/env python3

import os
import math

import yaml
import rclpy

from rclpy.node import Node
from rclpy.action import ActionClient

from ament_index_python.packages import get_package_share_directory

from std_msgs.msg import String
from sensor_msgs.msg import JointState

from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

from ros_gz_interfaces.srv import SetEntityPose, DeleteEntity
from tf2_ros import Buffer, TransformListener
from ros_gz_interfaces.srv import DeleteEntity

class TaskManager(Node):

    def __init__(self):
        super().__init__("task_manager")

        # ======================================================
        # Load configuration
        # ======================================================

        package_share = get_package_share_directory(
            "waste_perception"
        )

        config_file = os.path.join(
            package_share,
            "config",
            "system.yaml"
        )

        with open(config_file, "r") as file:
            self.config = yaml.safe_load(file)

        # ======================================================
        # Arm
        # ======================================================

        self.arm_joint_names = self.config["arm"]["joint_names"]

        waypoints = self.config["arm"]["waypoints"]

        # Ignore intentionally empty waypoints such as blue_pre_bin: {}
        self.waypoints = {
            name: waypoint
            for name, waypoint in waypoints.items()
            if waypoint
        }

        # ======================================================
        # Gripper
        # ======================================================

        self.gripper_joint = self.config["gripper"]["joint_name"]

        self.gripper_open = float(
            self.config["gripper"]["open"]
        )

        self.gripper_close = float(
            self.config["gripper"]["close"]
        )

        # ======================================================
        # Runtime state
        # ======================================================

        self.current_joint_state = None

        # True while a complete sorting operation is running.
        # Vision messages are ignored while busy.
        self.busy = False
        self.armed = True

        self.active_color = None
        self.object_name = None

        # ======================================================
        # Fake grasp
        # ======================================================

        self.tf_buffer = Buffer()

        self.tf_listener = TransformListener(
            self.tf_buffer,
            self
        )

        self.set_pose_client = self.create_client(
            SetEntityPose,
            "/world/waste_sorting_cell/set_pose"
        )

        self.delete_entity_client = self.create_client(
            DeleteEntity,
            "/world/waste_sorting_cell/remove"
        )

        self.object_follow_timer = None
        self.pose_request_in_flight = False

        # Actual finger links from the URDF.
        self.right_finger_link = "right_gripper_fingure"
        self.left_finger_link = "left_gripper_fingure"
        self.tool_link = "link_4"

        # Move the fake object slightly beyond the finger midpoint
        # in the direction from link_4 toward the jaws.
        self.grasp_offset = 0.042  # 5 cm

        # Robot Gazebo spawn pose.
        self.robot_x = 0.0
        self.robot_y = 0.5
        self.robot_z = 0.7
        self.robot_yaw = -1.5708

        # ======================================================
        # Subscribers
        # ======================================================

        self.vision_sub = self.create_subscription(
            String,
            "/vision/result",
            self.vision_callback,
            10
        )

        self.joint_state_sub = self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            10
        )

        # ======================================================
        # Action clients
        # ======================================================

        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory"
        )

        self.gripper_client = ActionClient(
            self,
            FollowJointTrajectory,
            "/gripper_controller/follow_joint_trajectory"
        )

        self.get_logger().info("Task manager ready.")
        self.get_logger().info("Waiting for vision result...")

    # ==========================================================
    # Joint state
    # ==========================================================

    def joint_state_callback(self, msg):
        self.current_joint_state = msg

    # ==========================================================
    # Vision
    # ==========================================================

    def vision_callback(self, msg):

        detected = msg.data.strip().lower()

        self.get_logger().info(
            f"Vision result: {detected}"
        )

        # Once a sorting cycle has started, completely ignore
        # camera updates until the cycle finishes.
        if self.busy:
            return

        if detected == "unknown":
            self.armed = True
            return

        if detected not in ("red", "blue"):
            return

        if not self.armed:
            return

        self.active_color = detected
        self.object_name = f"{detected}_object"

        self.busy = True
        self.armed = False

        self.get_logger().info(
            f"{detected.upper()} object detected."
        )

        self.start_sequence()

    # ==========================================================
    # Main sequence
    # ==========================================================

    def start_sequence(self):

        if self.current_joint_state is None:
            self.get_logger().error(
                "No joint state available."
            )
            self.reset_task()
            return

        self.open_gripper()

    # ==========================================================
    # Gripper OPEN
    # ==========================================================

    def open_gripper(self):

        if not self.gripper_client.wait_for_server(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "Gripper action server not available."
            )
            self.reset_task()
            return

        self.get_logger().info("Opening gripper...")

        goal = FollowJointTrajectory.Goal()

        goal.trajectory.joint_names = [
            self.gripper_joint
        ]

        point = JointTrajectoryPoint()
        point.positions = [self.gripper_open]
        point.time_from_start.sec = 1
        point.time_from_start.nanosec = 0

        goal.trajectory.points = [point]

        future = self.gripper_client.send_goal_async(goal)
        future.add_done_callback(self.open_goal_response)

    # ==========================================================
    # OPEN response
    # ==========================================================

    def open_goal_response(self, future):

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error(
                "Gripper OPEN rejected."
            )
            self.reset_task()
            return

        self.get_logger().info(
            "Gripper OPEN accepted."
        )

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.open_finished)

    # ==========================================================
    # OPEN finished
    # ==========================================================

    def open_finished(self, future):

        self.get_logger().info(
            "Gripper is open."
        )

        self.move_to_waypoint(
            "pre_pick",
            self.pre_pick_finished
        )

    # ==========================================================
    # PRE_PICK finished
    # ==========================================================

    def pre_pick_finished(self):

        self.get_logger().info(
            "PRE_PICK reached."
        )

        self.move_to_waypoint(
            "pick",
            self.pick_finished
        )

    # ==========================================================
    # PICK finished
    # ==========================================================

    def pick_finished(self):

        self.get_logger().info(
            "PICK reached."
        )

        self.close_gripper()

    # ==========================================================
    # Gripper CLOSE
    # ==========================================================

    def close_gripper(self):

        if not self.gripper_client.wait_for_server(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "Gripper action server not available."
            )
            self.reset_task()
            return

        self.get_logger().info(
            f"Closing gripper to {self.gripper_close}..."
        )

        goal = FollowJointTrajectory.Goal()

        goal.trajectory.joint_names = [
            self.gripper_joint
        ]

        point = JointTrajectoryPoint()
        point.positions = [self.gripper_close]
        point.time_from_start.sec = 1
        point.time_from_start.nanosec = 0

        goal.trajectory.points = [point]

        future = self.gripper_client.send_goal_async(goal)
        future.add_done_callback(self.close_goal_response)

    # ==========================================================
    # CLOSE response
    # ==========================================================

    def close_goal_response(self, future):

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error(
                "Gripper CLOSE rejected."
            )
            self.reset_task()
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.close_finished)

    # ==========================================================
    # CLOSE finished
    # ==========================================================

    def close_finished(self, future):

        self.get_logger().info(
            "Gripper closed."
        )

        # Start fake grasp before moving the arm.
        self.attach_object()

        self.move_to_waypoint(
            "lift",
            self.lift_finished
        )

    # ==========================================================
    # LIFT finished
    # ==========================================================

    def lift_finished(self):

        self.get_logger().info(
            "LIFT reached."
        )

        if self.active_color == "red":

            self.get_logger().info(
                "Following RED motion."
            )

            self.move_to_waypoint(
                "red_pre_bin",
                self.red_pre_bin_finished
            )

        elif self.active_color == "blue":

            self.get_logger().info(
                "Following BLUE motion."
            )

            self.move_to_waypoint(
                "blue_pre_bin",
                self.blue_pre_bin_finished
            )

    # ==========================================================
    # RED pre-bin finished
    # ==========================================================

    def red_pre_bin_finished(self):

        self.get_logger().info(
            "RED_PRE_BIN reached."
        )

        self.move_to_waypoint(
            "red_drop",
            self.red_drop_finished
        )

    # ==========================================================
    # BLUE pre-bin finished
    # ==========================================================

    def blue_pre_bin_finished(self):

        self.get_logger().info(
            "BLUE_PRE_BIN reached."
        )

        self.move_to_waypoint(
            "blue_drop",
            self.blue_drop_finished
        )

    # ==========================================================
    # RED drop finished
    # ==========================================================

    def red_drop_finished(self):

        self.get_logger().info(
            "RED_DROP reached."
        )

        self.release_object()

    # ==========================================================
    # BLUE drop finished
    # ==========================================================

    def blue_drop_finished(self):

        self.get_logger().info(
            "BLUE_DROP reached."
        )

        self.release_object()

    # ==========================================================
    # RELEASE
    # ==========================================================

    def object_deleted(self, future):

        try:
            response = future.result()

            self.get_logger().info(
                f"Object delete result: {response}"
            )

        except Exception as error:

            self.get_logger().error(
                f"Failed to delete object: {error}"
            )

            return

        # Only continue after Gazebo confirms deletion.
        self.open_gripper_after_drop()

    def release_object(self):

        # Stop fake object following first.
        self.detach_object()

        if self.object_name is None:
            self.get_logger().error(
                "No object name available for deletion."
            )
            self.open_gripper_after_drop()
            return

        if not self.delete_entity_client.wait_for_service(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "DeleteEntity service not available."
            )
            return

        self.get_logger().info(
            f"DROP: deleting {self.object_name}"
        )

        request = DeleteEntity.Request()

        request.entity.name = self.object_name
        request.entity.type = 2   # MODEL

        future = self.delete_entity_client.call_async(request)

        future.add_done_callback(
            self.object_deleted
        )

    # ==========================================================
    # OPEN after drop
    # ==========================================================

    def open_gripper_after_drop(self):

        if not self.gripper_client.wait_for_server(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "Gripper action server not available."
            )
            self.reset_task()
            return

        goal = FollowJointTrajectory.Goal()

        goal.trajectory.joint_names = [
            self.gripper_joint
        ]

        point = JointTrajectoryPoint()
        point.positions = [self.gripper_open]
        point.time_from_start.sec = 1
        point.time_from_start.nanosec = 0

        goal.trajectory.points = [point]

        future = self.gripper_client.send_goal_async(goal)
        future.add_done_callback(self.release_open_response)

    # ==========================================================
    # Release OPEN response
    # ==========================================================

    def release_open_response(self, future):

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error(
                "Gripper release rejected."
            )
            self.reset_task()
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            self.release_open_finished
        )

    # ==========================================================
    # Release finished
    # ==========================================================

    def release_open_finished(self, future):

        self.get_logger().info(
            "Object released."
        )

        self.move_to_waypoint(
            "home",
            self.home_finished
        )

    # ==========================================================
    # HOME finished
    # ==========================================================

    def home_finished(self):

        self.get_logger().info(
            "HOME reached."
        )

        self.reset_task()

    # ==========================================================
    # Generic arm waypoint motion
    # ==========================================================

    def move_to_waypoint(
        self,
        waypoint_name,
        finished_callback
    ):

        if waypoint_name not in self.waypoints:
            self.get_logger().error(
                f"Waypoint '{waypoint_name}' "
                f"is missing from system.yaml."
            )
            self.reset_task()
            return

        if not self.arm_client.wait_for_server(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "Arm action server not available."
            )
            self.reset_task()
            return

        if self.current_joint_state is None:
            self.get_logger().error(
                "No current joint state."
            )
            self.reset_task()
            return

        current = {
            name: position
            for name, position in zip(
                self.current_joint_state.name,
                self.current_joint_state.position
            )
        }

        try:
            current_positions = [
                float(current[name])
                for name in self.arm_joint_names
            ]

            target = self.waypoints[waypoint_name]

            target_positions = [
                float(target[name])
                for name in self.arm_joint_names
            ]

        except KeyError as error:
            self.get_logger().error(
                f"Joint '{error.args[0]}' is missing."
            )
            self.reset_task()
            return

        goal = FollowJointTrajectory.Goal()

        goal.trajectory.joint_names = (
            self.arm_joint_names
        )

        start_point = JointTrajectoryPoint()
        start_point.positions = current_positions
        start_point.time_from_start.sec = 0
        start_point.time_from_start.nanosec = 100000000

        target_point = JointTrajectoryPoint()
        target_point.positions = target_positions
        target_point.time_from_start.sec = 6
        target_point.time_from_start.nanosec = 0

        goal.trajectory.points = [
            start_point,
            target_point
        ]

        self.get_logger().info(
            f"Moving to {waypoint_name.upper()}..."
        )

        future = self.arm_client.send_goal_async(goal)

        future.add_done_callback(
            lambda future_result:
                self.arm_goal_response(
                    future_result,
                    finished_callback
                )
        )

    # ==========================================================
    # Arm goal response
    # ==========================================================

    def arm_goal_response(
        self,
        future,
        finished_callback
    ):

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error(
                "Arm goal rejected."
            )
            self.reset_task()
            return

        self.get_logger().info(
            "Arm goal accepted."
        )

        result_future = goal_handle.get_result_async()

        result_future.add_done_callback(
            lambda result_future:
                self.arm_goal_finished(
                    result_future,
                    finished_callback
                )
        )


    def arm_goal_finished(
        self,
        future,
        finished_callback
    ):

        result = future.result().result

        if result.error_code != 0:
            self.get_logger().error(
                f"Arm trajectory failed. "
                f"error_code={result.error_code}"
            )

            self.reset_task()
            return

        self.get_logger().info(
            "Arm trajectory completed successfully."
        )

        finished_callback()

    # ==========================================================
    # Attach object
    # ==========================================================

    def attach_object(self):

        if self.object_name is None:
            return

        if not self.set_pose_client.wait_for_service(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "SetEntityPose service not available."
            )
            return

        self.get_logger().info(
            f"FAKE GRASP: {self.object_name} attached."
        )

        if self.object_follow_timer is None:
            self.object_follow_timer = self.create_timer(
                0.05,
                self.update_object_pose
            )

        # Move it to the jaws immediately.
        self.update_object_pose()

    # ==========================================================
    # Follow jaw midpoint
    # ==========================================================

    def update_object_pose(self):

        if self.object_name is None:
            return

        if self.pose_request_in_flight:
            return

        try:
            # Finger transforms in robot-relative BASE_LINK frame.
            right_tf = self.tf_buffer.lookup_transform(
                "base_link",
                self.right_finger_link,
                rclpy.time.Time()
            )

            left_tf = self.tf_buffer.lookup_transform(
                "base_link",
                self.left_finger_link,
                rclpy.time.Time()
            )

            # link_4 gives us the direction from the tool body
            # toward the gripper jaws.
            tool_tf = self.tf_buffer.lookup_transform(
                "base_link",
                self.tool_link,
                rclpy.time.Time()
            )

        except Exception:
            return

        # ======================================================
        # Finger midpoint in BASE_LINK frame
        # ======================================================

        right = right_tf.transform.translation
        left = left_tf.transform.translation
        tool = tool_tf.transform.translation

        bx = (right.x + left.x) / 2.0
        by = (right.y + left.y) / 2.0
        bz = (right.z + left.z) / 2.0

        # ======================================================
        # Move object a little OUTWARD from the jaws
        #
        # Direction:
        #     link_4 -> finger midpoint
        #
        # This is better than guessing a world X/Y/Z offset and
        # automatically follows the gripper orientation.
        # ======================================================

        dx = bx - tool.x
        dy = by - tool.y
        dz = bz - tool.z

        length = math.sqrt(
            dx * dx +
            dy * dy +
            dz * dz
        )

        if length > 1e-6:
            bx += self.grasp_offset * dx / length
            by += self.grasp_offset * dy / length
            bz += self.grasp_offset * dz / length

        # ======================================================
        # Convert BASE_LINK -> GAZEBO WORLD
        #
        # Robot spawn:
        #     x   = 0.0
        #     y   = 0.5
        #     z   = 0.7
        #     yaw = -1.5708
        # ======================================================

        cos_yaw = math.cos(self.robot_yaw)
        sin_yaw = math.sin(self.robot_yaw)

        x = (
            self.robot_x +
            cos_yaw * bx -
            sin_yaw * by
        )

        y = (
            self.robot_y +
            sin_yaw * bx +
            cos_yaw * by
        )

        z = self.robot_z + bz

        # ======================================================
        # Set object pose
        # ======================================================

        request = SetEntityPose.Request()

        request.entity.name = self.object_name

        request.pose.position.x = x
        request.pose.position.y = y
        request.pose.position.z = z

        # Keep the cube upright.
        request.pose.orientation.x = 0.0
        request.pose.orientation.y = 0.0
        request.pose.orientation.z = 0.0
        request.pose.orientation.w = 1.0

        self.pose_request_in_flight = True

        future = self.set_pose_client.call_async(request)

        future.add_done_callback(
            self.object_pose_finished
        )

    # ==========================================================
    # Pose update finished
    # ==========================================================

    def object_pose_finished(self, future):

        self.pose_request_in_flight = False

    # ==========================================================
    # Detach object
    # ==========================================================

    def detach_object(self):

        if self.object_follow_timer is not None:
            self.object_follow_timer.cancel()
            self.object_follow_timer = None

        self.pose_request_in_flight = False

        self.get_logger().info(
            "FAKE GRASP: object released."
        )

    # ==========================================================
    # Reset
    # ==========================================================

    def reset_task(self):

        self.detach_object()

        self.busy = False
        self.armed = True

        self.active_color = None
        self.object_name = None


def main(args=None):

    rclpy.init(args=args)

    node = TaskManager()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

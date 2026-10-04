#!/usr/bin/env python3

import rclpy

from rclpy.node import Node

from sensor_msgs.msg import JointState


JOINT_NAMES = [
    "base_link_link_1",
    "link_1_link_2",
    "link_2_link_3",
    "link_3_link_4",
]


class WaypointRecorder(Node):

    def __init__(self):

        super().__init__(
            "record_waypoint"
        )

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_callback,
            10,
        )

        self.current_positions = {}

        self.get_logger().info(
            "Waypoint recorder started."
        )

        self.get_logger().info(
            "Waiting for joint states..."
        )

    def joint_callback(self, msg):

        for name, position in zip(
            msg.name,
            msg.position,
        ):

            if name in JOINT_NAMES:

                self.current_positions[name] = position

        if all(
            joint in self.current_positions
            for joint in JOINT_NAMES
        ):

            self.print_positions()

            self.destroy_subscription(
                self.subscriptions[0]
                if self.subscriptions
                else None
            )

    def print_positions(self):

        print()
        print(
            "=========================================="
        )
        print(
            "Current waypoint"
        )
        print(
            "=========================================="
        )

        for joint in JOINT_NAMES:

            print(
                f"{joint}: "
                f"{self.current_positions[joint]:.6f}"
            )

        print(
            "=========================================="
        )

        rclpy.shutdown()


def main(args=None):

    rclpy.init(args=args)

    node = WaypointRecorder()

    rclpy.spin(node)


if __name__ == "__main__":
    main()

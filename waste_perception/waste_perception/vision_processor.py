#!/usr/bin/env python3

import cv2
import rclpy

from cv_bridge import CvBridge

from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Image
from std_msgs.msg import String


class VisionProcessor(Node):

    def __init__(self):

        super().__init__("vision_processor")

        # -----------------------------------------------------
        # Parameters
        # -----------------------------------------------------

        self.declare_parameter(
            "image_topic",
            "/sorting_camera/image",
        )

        self.declare_parameter(
            "result_topic",
            "/vision/result",
        )

        self.declare_parameter(
            "min_pixels",
            200,
        )

        self.declare_parameter(
            "process_every_n_frames",
            3,
        )

        self.image_topic = (
            self.get_parameter("image_topic")
            .value
        )

        self.result_topic = (
            self.get_parameter("result_topic")
            .value
        )

        self.min_pixels = int(
            self.get_parameter("min_pixels")
            .value
        )

        self.process_every_n_frames = int(
            self.get_parameter(
                "process_every_n_frames"
            ).value
        )

        # -----------------------------------------------------
        # OpenCV bridge
        # -----------------------------------------------------

        self.bridge = CvBridge()

        # -----------------------------------------------------
        # State
        # -----------------------------------------------------

        self.frame_count = 0
        self.last_result = "unknown"

        # -----------------------------------------------------
        # ROS subscriber
        # -----------------------------------------------------

        self.image_subscriber = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )

        # -----------------------------------------------------
        # ROS publisher
        # -----------------------------------------------------

        self.result_publisher = self.create_publisher(
            String,
            self.result_topic,
            10,
        )

        self.get_logger().info(
            "Vision processor started."
        )

        self.get_logger().info(
            f"Image topic: {self.image_topic}"
        )

        self.get_logger().info(
            f"Result topic: {self.result_topic}"
        )

    # =========================================================
    # Image callback
    # =========================================================

    def image_callback(self, msg):

        self.frame_count += 1

        # Process only every Nth frame
        if (
            self.frame_count
            % self.process_every_n_frames
            != 0
        ):
            return

        try:

            image = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="bgr8",
            )

        except Exception as error:

            self.get_logger().error(
                f"Failed to convert image: {error}"
            )

            return

        result = self.detect_color(image)

        # -----------------------------------------------------
        # Publish result
        # -----------------------------------------------------

        output = String()

        output.data = result

        self.result_publisher.publish(output)

        # -----------------------------------------------------
        # Log only when result changes
        # -----------------------------------------------------

        if result != self.last_result:

            self.get_logger().info(
                f"Vision result: {result}"
            )

            self.last_result = result

    # =========================================================
    # Color processing
    # =========================================================

    def detect_color(self, image):

        # -----------------------------------------------------
        # Convert BGR → HSV
        # -----------------------------------------------------

        hsv = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2HSV,
        )

        # -----------------------------------------------------
        # Red
        #
        # Red wraps around the HSV hue range, so two masks
        # are required.
        # -----------------------------------------------------

        red_lower_1 = (
            0,
            100,
            80,
        )

        red_upper_1 = (
            10,
            255,
            255,
        )

        red_lower_2 = (
            170,
            100,
            80,
        )

        red_upper_2 = (
            180,
            255,
            255,
        )

        red_mask_1 = cv2.inRange(
            hsv,
            red_lower_1,
            red_upper_1,
        )

        red_mask_2 = cv2.inRange(
            hsv,
            red_lower_2,
            red_upper_2,
        )

        red_mask = cv2.bitwise_or(
            red_mask_1,
            red_mask_2,
        )

        # -----------------------------------------------------
        # Blue
        # -----------------------------------------------------

        blue_lower = (
            100,
            100,
            80,
        )

        blue_upper = (
            130,
            255,
            255,
        )

        blue_mask = cv2.inRange(
            hsv,
            blue_lower,
            blue_upper,
        )

        # -----------------------------------------------------
        # Remove small noise
        # -----------------------------------------------------

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (5, 5),
        )

        red_mask = cv2.morphologyEx(
            red_mask,
            cv2.MORPH_OPEN,
            kernel,
        )

        red_mask = cv2.morphologyEx(
            red_mask,
            cv2.MORPH_CLOSE,
            kernel,
        )

        blue_mask = cv2.morphologyEx(
            blue_mask,
            cv2.MORPH_OPEN,
            kernel,
        )

        blue_mask = cv2.morphologyEx(
            blue_mask,
            cv2.MORPH_CLOSE,
            kernel,
        )

        # -----------------------------------------------------
        # Count detected pixels
        # -----------------------------------------------------

        red_pixels = cv2.countNonZero(
            red_mask
        )

        blue_pixels = cv2.countNonZero(
            blue_mask
        )

        # -----------------------------------------------------
        # Classification
        # -----------------------------------------------------

        if (
            red_pixels < self.min_pixels
            and blue_pixels < self.min_pixels
        ):

            return "unknown"

        if red_pixels > blue_pixels:

            return "red"

        if blue_pixels > red_pixels:

            return "blue"

        return "unknown"


def main(args=None):

    rclpy.init(args=args)

    node = VisionProcessor()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == "__main__":
    main()

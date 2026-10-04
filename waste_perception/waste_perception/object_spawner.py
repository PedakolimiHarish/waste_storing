#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from ros_gz_interfaces.srv import SpawnEntity


class ObjectSpawner(Node):

    def __init__(self):
        super().__init__("object_spawner")

        self.spawn_client = self.create_client(
            SpawnEntity,
            "/world/waste_sorting_cell/create",
        )

        # -----------------------------------------------------
        # Parameters
        # -----------------------------------------------------

        self.declare_parameter("color", "red")

        self.color = (
            self.get_parameter("color")
            .get_parameter_value()
            .string_value
            .lower()
        )

        self.get_logger().info(
            f"Object spawner started. Selected color: {self.color}"
        )

    # =========================================================
    # Create colored object SDF
    # =========================================================

    def create_object_sdf(self, name, color):

        # -----------------------------------------------------
        # Select color
        # -----------------------------------------------------

        if color == "red":
            r = 1.0
            g = 0.0
            b = 0.0

        elif color == "blue":
            r = 0.0
            g = 0.0
            b = 1.0

        else:
            raise ValueError(
                "Color must be 'red' or 'blue'."
            )

        # -----------------------------------------------------
        # Object size
        # 0.04 = 40 mm cube
        # -----------------------------------------------------

        mass = 0.1
        size = 0.04

        # -----------------------------------------------------
        # Inertia
        # -----------------------------------------------------

        inertia = (
            (1.0 / 6.0)
            * mass
            * size
            * size
        )

        # -----------------------------------------------------
        # SDF
        # -----------------------------------------------------
        #
        # No collision element:
        #   -> object does not physically collide
        #
        # gravity=false:
        #   -> object will not fall
        #
        # static=false:
        #   -> Gazebo still treats it as a movable entity
        #   -> useful for SetEntityPose
        #
        # -----------------------------------------------------

        return f"""
<?xml version="1.0"?>

<sdf version="1.9">

    <model name="{name}">

        <static>true</static>

        <link name="link">

            <gravity>false</gravity>

            <self_collide>false</self_collide>

            <inertial>

                <mass>{mass}</mass>

                <inertia>

                    <ixx>{inertia}</ixx>
                    <ixy>0.0</ixy>
                    <ixz>0.0</ixz>

                    <iyy>{inertia}</iyy>
                    <iyz>0.0</iyz>

                    <izz>{inertia}</izz>

                </inertia>

            </inertial>

            <!-- ========================================= -->
            <!-- Visual only                               -->
            <!-- No collision                             -->
            <!-- ========================================= -->

            <visual name="visual">

                <geometry>

                    <box>

                        <size>{size} {size} {size}</size>

                    </box>

                </geometry>

                <material>

                    <!-- Main color -->
                    <ambient>
                        {r} {g} {b} 1
                    </ambient>

                    <diffuse>
                        {r} {g} {b} 1
                    </diffuse>

                    <!-- Makes color clearly visible -->
                    <emissive>
                        {r} {g} {b} 1
                    </emissive>

                    <specular>
                        0.1 0.1 0.1 1
                    </specular>

                </material>

            </visual>

        </link>

    </model>

</sdf>
"""

    # =========================================================
    # Spawn object
    # =========================================================

    def spawn_object(self, name, sdf, x, y, z):

        self.get_logger().info(
            f"Spawning {name} at "
            f"x={x:.3f}, "
            f"y={y:.3f}, "
            f"z={z:.3f}"
        )

        # -----------------------------------------------------
        # Wait for Gazebo spawn service
        # -----------------------------------------------------

        while not self.spawn_client.wait_for_service(
            timeout_sec=1.0
        ):
            self.get_logger().info(
                "Waiting for Gazebo spawn service..."
            )

        # -----------------------------------------------------
        # Create request
        # -----------------------------------------------------

        request = SpawnEntity.Request()

        request.entity_factory.name = name
        request.entity_factory.sdf = sdf

        request.entity_factory.pose.position.x = x
        request.entity_factory.pose.position.y = y
        request.entity_factory.pose.position.z = z

        request.entity_factory.pose.orientation.x = 0.0
        request.entity_factory.pose.orientation.y = 0.0
        request.entity_factory.pose.orientation.z = 0.0
        request.entity_factory.pose.orientation.w = 1.0

        request.entity_factory.relative_to = "world"
        request.entity_factory.allow_renaming = False

        # -----------------------------------------------------
        # Send request
        # -----------------------------------------------------

        future = self.spawn_client.call_async(request)

        rclpy.spin_until_future_complete(
            self,
            future,
        )

        # -----------------------------------------------------
        # Check result
        # -----------------------------------------------------

        if future.result() is None:

            self.get_logger().error(
                "Failed to call Gazebo spawn service."
            )

            return False

        response = future.result()

        if response.success:

            self.get_logger().info(
                f"Successfully spawned {name}"
            )

            return True

        self.get_logger().error(
            f"Failed to spawn {name}: "
            f"{response.status_message}"
        )

        return False


# =============================================================
# Main
# =============================================================

def main(args=None):

    rclpy.init(args=args)

    node = ObjectSpawner()

    # ---------------------------------------------------------
    # Validate color
    # ---------------------------------------------------------

    if node.color not in ("red", "blue"):

        node.get_logger().error(
            "Invalid color. Use: red or blue"
        )

        node.destroy_node()
        rclpy.shutdown()
        return

    # ---------------------------------------------------------
    # Object name
    # ---------------------------------------------------------

    object_name = f"{node.color}_object"

    # ---------------------------------------------------------
    # Create SDF
    # ---------------------------------------------------------

    object_sdf = node.create_object_sdf(
        object_name,
        node.color,
    )

    # ---------------------------------------------------------
    # Spawn position
    # ---------------------------------------------------------

    success = node.spawn_object(
        name=object_name,
        sdf=object_sdf,
        x=0.0,
        y=-0.01,
        z=0.77,
    )

    if success:

        node.get_logger().info(
            "Object spawning complete."
        )

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()

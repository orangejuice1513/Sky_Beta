"""
control_node.py: contains the heartbeat, arming sequence, and trajectory setpoints

"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import TrajectorySetpoint, VehicleCommand, VehicleStatus, OffboardControlMode

class OffboardControl(Node):
    # this node is called offboard_control in the ros2 node list 
    def __init__(self):
        super().__init__('offboard_control')
        self.target_position = [0.0, 0.0, -5.0] # change this later 
        self.target_yaw = 0.0 # change this later 

        # best effort (UDP) 
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, #best effort instead of reliable(TCP)  
            durability=DurabilityPolicy.TRANSIENT_LOCAL, #save the last message
            history=HistoryPolicy.KEEP_LAST, #only keep last message
            depth=1
        )

        # --- PUBLISHERS ---
        self.trajectory_publisher = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile)
        self.offboard_control_node_publisher = self.create_publisher(OffboardControlMode, 'fmu/in/offboard_control_mode', qos_profile) 
        # --- SUBSCRIBERS ---
        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus, 
            '/fmu/out/vehicle_status', 
            self.vehicle_status_callback, 
            qos_profile
        )

        # --- TIMER ---
        # PX4 needs commands at least 10Hz (0.1 seconds)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX
        self.arming_state = VehicleStatus.ARMING_STATE_DISARMED
    
        # Counter to wait for heartbeat
        self.offboard_setpoint_counter = 0

    def vehicle_status_callback(self, msg):
        """
        stores vehicle status into class variables 
        """
        self.vehicle_status = msg 
        self.nav_state = msg.nav_state #current flight mode 
        self.arming_state = msg.arming_state #motors armed? 

    def timer_callback(self):
        """
        main loop: publishes TrajectorySetpoint, checks the current state and decides if it needs to be fixed 
        """
        self.publish_offboard_control_mode()
        self.publish_trajectory_setpoint()
        if self.offboard_setpoint_counter == 10: 
            self.engage_offboard_mode()
            self.arm()
        if self.offboard_setpoint_counter > 10 and self.offboard_setpoint_counter % 10 == 0:
            if self.nav_state != VehicleStatus.NAVIGATION_STATE_OFFBOARD:
                self.engage_offboard_mode()
            if self.arming_state != VehicleStatus.ARMING_STATE_ARMED:
                self.arm() 
        if self.offboard_setpoint_counter < 100:
            self.offboard_setpoint_counter += 1 

    def arm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
        self.get_logger().info("Arm command sent")

    def engage_offboard_mode(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1., 6.)
        self.get_logger().info("Switching to offboard mode")

    def publish_offboard_control_mode(self):
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(msg)

    def update_target(self, x, y, z):
        """
        updates the destination coordinates 
        """
        self.target_position = [x, y, z]
        self.get_logger().info(f"new target: {x}, {y}, {z}")

    def publish_trajectory_setpoint(self):
        """
        publishes target state 
        """
        msg = TrajectorySetpoint()
        msg.position = self.target_position
        msg.yaw = self.target_yaw 
        msg.velocity = [float('nan'), float('nan'), float('nan')]
        msg.acceleration = [float('nan'), float('nan'), float('nan')]
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)

        self.trajectory_publisher.publish(msg)

    def publish_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.param1 = param1
        msg.param2 = param2
        msg.command = command
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = OffboardControl()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()




# subscriber.py
import rclpy
from rclpy.node import Node
from task_one_msgs.msg import TaskOne

class SpeedCalculator(Node):
    
    def __init__(self):
        super().__init__('subscriber_node')
        self.subscription = self.create_subscription(
            TaskOne,
            '/taskone',
            self.listener_callback,
            10)
        self.get_logger().info('Speed Calculator Node has been started and is listening.')

    def listener_callback(self, msg):
        
        angular_velocity = msg.angvel
        radius = msg.radius

        longitudinal_speed = angular_velocity * radius
        self.get_logger().info(f'Received: angvel={angular_velocity:.2f}, radius={radius:.2f}')
        self.get_logger().info(f'--> Calculated Longitudinal Speed: {longitudinal_speed:.2f} m/s')

def main(args=None):
    rclpy.init(args=args)#??
    speed_calculator = SpeedCalculator()
    rclpy.spin(speed_calculator)
    speed_calculator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__': #??
    main()
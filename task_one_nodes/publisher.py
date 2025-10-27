import rclpy
from rclpy.node import Node
from task_one_msgs.msg import TaskOne
import time  

class WheelPublisher(Node):
   
    def __init__(self):
        super().__init__('publisher_node')
        self.publisher_ = self.create_publisher(TaskOne, '/taskone',11)#??
        self.get_logger().info('Wheel Data Publisher Node has been started.')
        timer_period = 0.1  
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        try:
            
            angvel_str = input("Enter angular velocity (rad/s): ")
            radius_str = input("Enter wheel radius (m): ")
            angvel = float(angvel_str)
            radius = float(radius_str)

            msg = TaskOne()
            msg.angvel = angvel
            msg.radius = radius

            self.publisher_.publish(msg)
            self.get_logger().info(f'Publishing: angvel={msg.angvel:.2f}, radius={msg.radius:.2f}')

        except ValueError:
            self.get_logger().error('Invalid input. Please enter numeric values.')
        except KeyboardInterrupt:
            pass


def main(args=None):
    rclpy.init(args=args)#??
    wheel_publisher = WheelPublisher()
    
    try:
        rclpy.spin(wheel_publisher)
    except KeyboardInterrupt:
        pass
    
    wheel_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
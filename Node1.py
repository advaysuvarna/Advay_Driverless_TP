import rclpy
from rclpy.node import Node
import sys
sys.path.append('/root/ros2_ws/src/task_two_msg')
from task_two_msg import Tasktwo

#This node only PUBLISHES THE INPUT IT GETS 

class PalindromePublisher(Node):
    def __init__(self):
        super().__init__('publisher_node')
        self.publisher_ = self.create_publisher(Tasktwo, '/tasktwo', 10)
        self.get_logger().info('String input Publisher Node has been started.')

    def publish_input(self, user_input):
        msg = Tasktwo()
        msg.palindrome = user_input
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: {msg.palindrome}')


def main(args=None):
    rclpy.init(args=args)
    node = PalindromePublisher()

    try:
        while rclpy.ok():
            s = input("Enter a string to check for palindrome: ")
            node.publish_input(s)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
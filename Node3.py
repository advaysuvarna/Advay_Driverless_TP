import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

class Output(Node):  
    def __init__(self):
        super().__init__('subscriber_node')
        self.subscription = self.create_subscription(Int32,'/flag',self.listener_callback,10)
        self.get_logger().info('Node3 started and waiting for flag from Node2')

    def listener_callback(self, msg):
        if msg.data == 1:
            self.get_logger().info("Yes — it's a palindrome.")
        else:
            self.get_logger().info("No — not a palindrome.")

def main(args=None):
    rclpy.init(args=args)
    node = Output()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

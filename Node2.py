import rclpy
from rclpy.node import Node
from task_two_msg.msg import Tasktwo
from std_msgs.msg import Int32

#this guys supo recieve the input from node1 and send 1 or 0 to node3

class Palindrome_checker(Node):
    
    def __init__(self):
        super().__init__('subscriber_node')
        self.subscription = self.create_subscription(Tasktwo,'/tasktwo',self.listener_callback,10)
        self.flag_publisher = self.create_publisher(Int32, '/flag', 10)
        self.get_logger().info('Checking if palindrome, pls wait ')

    def listener_callback(self, msg):
        check = msg.palindrome
        self.get_logger().info(f'Received your input: {check}')
        x = check[::-1]
        flag_msg = Int32()
        if check == x:
            flag_msg.data = 1
        else:
            flag_msg.data = 0
        self.flag_publisher.publish(flag_msg)

def main(args=None):
    rclpy.init(args=args)   
    palindromechecker = Palindrome_checker()
    rclpy.spin(palindromechecker)
    palindromechecker.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__': 
    main()
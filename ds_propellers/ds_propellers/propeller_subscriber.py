import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from std_srvs.srv import SetBool
from gpiozero import PWMOutputDevice, DigitalOutputDevice


class PropellerSubscriber(Node):
    def __init__(self):
        super().__init__('propeller_subscriber')

        self.declare_parameter('max_power_limit', 50)
        self.power_limit = self.get_parameter('max_power_limit').value

        self.is_armed = False  # Domyślnie silniki zablokowane

        # Konfiguracja pinów (GPIO)
        self.m1_pwm = PWMOutputDevice(17)
        self.m1_in1 = DigitalOutputDevice(27)
        self.m1_in2 = DigitalOutputDevice(22)

        self.m2_pwm = PWMOutputDevice(13)
        self.m2_in3 = DigitalOutputDevice(5)
        self.m2_in4 = DigitalOutputDevice(6)

        # Subskrypcja komend ruchu
        self.subscription = self.create_subscription(
            Int32MultiArray,
            'motor_commands',
            self.listener_callback,
            10)

        # Tworzymy usługę, która pozwala zdalnie zmieniać stan is_armed
        self.srv = self.create_service(SetBool, 'arm_robot', self.arm_callback)

        self.get_logger().info('Sterownik gotowy. STAN: ROZBROJONY (Czekam na serwis...)')

    def arm_callback(self, request, response):
        """
        Funkcja wywoływana, gdy ktoś zawoła serwis 'arm_robot'
        """
        self.is_armed = request.data

        if self.is_armed:
            response.success = True
            response.message = "Silniki UZBROJONE. Uwaga!"
            self.get_logger().info("UZBROJONO SILNIKI!")
        else:
            # Natychmiastowe zatrzymanie przy rozbrojeniu
            self.stop_motors()
            response.success = False
            response.message = "Silniki ROZBROJONE. Bezpiecznie."
            self.get_logger().info("Rozbrojono silniki.")

        return response

    def stop_motors(self):
        self.m1_pwm.off()
        self.m1_in1.off()
        self.m1_in2.off()
        self.m2_pwm.off()
        self.m2_in3.off()
        self.m2_in4.off()

    def set_motor(self, pwm_dev, in_a, in_b, command_power):
        # Ignoruj komendy, jeśli nie uzbrojony
        if not self.is_armed:
            self.stop_motors()  # Dla pewności
            return

        command_power = max(-100, min(100, command_power))
        scale_factor = self.power_limit / 100.0
        effective_speed = (abs(command_power) / 100.0) * scale_factor

        if command_power > 0:
            in_a.on()
            in_b.off()
            pwm_dev.value = effective_speed
        elif command_power < 0:
            in_a.off()
            in_b.on()
            pwm_dev.value = effective_speed
        else:
            in_a.off()
            in_b.off()
            pwm_dev.value = 0.0

    def listener_callback(self, msg):
        if len(msg.data) < 2:
            return

        if not self.is_armed:
            return

        cmd_long = msg.data[0]
        cmd_lat = msg.data[1]

        self.set_motor(self.m1_pwm, self.m1_in1, self.m1_in2, cmd_long)
        self.set_motor(self.m2_pwm, self.m2_in3, self.m2_in4, cmd_lat)


def main(args=None):
    rclpy.init(args=args)
    driver = PropellerSubscriber()
    try:
        rclpy.spin(driver)
    except KeyboardInterrupt:
        pass
    finally:
        driver.stop_motors()
        driver.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
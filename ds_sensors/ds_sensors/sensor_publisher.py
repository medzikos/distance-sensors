import rclpy
from rclpy.node import Node
from distance_msg.msg import Distance
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BOARD)


class SensorPublisher(Node):

    def __init__(self):
        super().__init__('sensor_publisher')

        # deklarujemy parametry charakteryzujące czujnik
        from rcl_interfaces.msg import ParameterDescriptor
        direction_parameter_descriptor = ParameterDescriptor(description='Parametr okresla azymut pomiaru odleglosci')
        self.declare_parameter('direction_parameter', 0, direction_parameter_descriptor)
        gpio_trigger_parameter_descriptor = ParameterDescriptor(description='Parametr okresla numer pinu GPIO dla TRIGGER')
        self.declare_parameter('gpio_trigger_parameter', 16, gpio_trigger_parameter_descriptor)
        gpio_echo_parameter_descriptor = ParameterDescriptor(description='Parametr okresla numer pinu GPIO dla Echo')
        self.declare_parameter('gpio_echo_parameter', 12, gpio_echo_parameter_descriptor)

        # tworzymy publisher publikujący na temacie 'distance_sensors'
        self.publisher_ = self.create_publisher(
            Distance, 
            'distance_sensors', 
            10
        )

        # odczytujemy wartości parametrów
        self.gpio_trigger = self.get_parameter('gpio_trigger_parameter').get_parameter_value().integer_value
        self.gpio_echo = self.get_parameter('gpio_echo_parameter').get_parameter_value().integer_value

        # Ustawiamy piny do komunikacji z czujnikiem
        GPIO.setup(self.gpio_trigger, GPIO.OUT)
        GPIO.setup(self.gpio_echo, GPIO.IN)
        GPIO.output(self.gpio_trigger, GPIO.LOW)
        time.sleep(2)

        # tworzymy timer
        self.timer_period = 0.05  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)


    def timer_callback(self):
        # odczytujemy wartości parametrów
        direction = self.get_parameter('direction_parameter').get_parameter_value().integer_value

        # wysyłamy sygnał aktywacji czujnika (TRIGGER)
        GPIO.output(self.gpio_trigger, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.gpio_trigger, GPIO.LOW)

        # zapisujemy czas początku sygnału zwrotnego z czujnika (ECHO)
        callback_start = time.time()
        while GPIO.input(self.gpio_echo)==0:
            pulse_start = time.time()
            # sprawdzamy czy pomiary się nie zazębiają
            if (pulse_start - callback_start) >= (self.timer_period - 0.01):
                self.get_logger().info('Brak danych z czujnika')
                return

        # zapisujemy czas końca sygnału zwrotnego z czujnika (ECHO)
        while GPIO.input(self.gpio_echo)==1:
            pulse_end = time.time()

        # obliczamy odległość od przeszkody w cm
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 2)

        # tworzymy i publikujemy wiadomość
        msg = Distance()
        msg.direction = direction
        msg.distance = distance
        self.publisher_.publish(msg)
        #self.get_logger().info('Azymut: "%s", Odleglosc: "%s"' % (msg.direction, msg.distance))


def main(args=None):
    try:
        rclpy.init(args=args)
        sensor_publisher = SensorPublisher()
        rclpy.spin(sensor_publisher)

        sensor_publisher.destroy_node()
        rclpy.shutdown()
    except KeyboardInterrupt:
        print("Pomiar zatrzymany przez użytkownika")
        GPIO.cleanup()


if __name__ == '__main__':
        main()

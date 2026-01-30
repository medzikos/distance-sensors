import sys
import math
import rclpy
from rclpy.node import Node
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import QTimer, Qt
from distance_msg.msg import Distance
from std_msgs.msg import Int32MultiArray
from std_srvs.srv import SetBool


class MotorSubscriber(Node):
    def __init__(self):
        super().__init__('motor_subscriber')
        self.readings = {}
        self.is_armed = False

        # tworzymy subscriber czytający temat 'distance_sensors'
        self.subscription = self.create_subscription(
            Distance,
            'distance_sensors',
            self.listener_callback,
            10)
        self.subscription

        # tworzymy publisher ustawień silników
        self.motor_publisher = self.create_publisher(Int32MultiArray, 'motor_commands', 10)

        # tworzymy klient serwisu do uzbrajania
        self.arm_client = self.create_client(SetBool, 'arm_robot')

    def publish_motor_commands(self, long_p, lat_p):
        msg = Int32MultiArray()
        msg.data = [int(long_p), int(lat_p)]
        self.motor_publisher.publish(msg)

    def listener_callback(self, msg):
        # odczytujemy dane z czujnika
        self.readings[int(msg.direction)] = msg.distance

    # metoda wysyłająca żądanie do serwisu
    def send_arm_request(self, state: bool):
        # sprawdzamy czy serwis jest dostępny
        if not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('Serwis arm_robot niedostępny!')
            return

        req = SetBool.Request()
        req.data = state

        future = self.arm_client.call_async(req)
        future.add_done_callback(self.arm_response_callback)

    # metoda przetwarzająca zwrotkę z serwisu
    def arm_response_callback(self, future):
        try:
            response = future.result()
            self.is_armed = response.success
            self.get_logger().info(f'Zmiana stanu: {response.message}')
        except Exception as e:
            self.get_logger().error(f'Błąd wywołania serwisu: {e}')


class DistanceGUI(QWidget):
    def __init__(self, ros_node):
        super().__init__()
        self.setWindowTitle("Czujniki odleglosci GUI")
        self.resize(1000, 800)
        self.ros_node = ros_node
        self.motor_powers = {0: 0, 90: 0, 180: 0, 270: 0}

        # Przycisk uzbrajania
        self.arm_button = QPushButton("UZBRÓJ (ARM)", self)
        # Ustawiamy przycisk w prawym górnym rogu
        self.arm_button.setGeometry(self.width() - 180, 20, 150, 40)
        self.arm_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.arm_button.clicked.connect(self.toggle_arm)

        # Timer do odświeżania GUI
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(100)

    # obsługa przycisku
    def toggle_arm(self):
        # Odwracamy żądany stan
        new_state = not self.ros_node.is_armed

        # Wysyłamy żądanie do ROS
        self.ros_node.send_arm_request(new_state)

        # Aktualizujemy wygląd przycisku
        if new_state:
            self.arm_button.setText("ROZBRÓJ (DISARM)")
            self.arm_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        else:
            self.arm_button.setText("UZBRÓJ (ARM)")
            self.arm_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")

    def update_gui(self):
        # Aktualizacja pozycji przycisku przy skalowaniu okna
        self.arm_button.move(self.width() - 180, 20)

        # Synchronizacja stanu przycisku z faktycznym stanem w Node
        # (na wypadek gdyby serwis odrzucił żądanie lub zmienił je ktoś inny)
        if self.ros_node.is_armed:
            self.arm_button.setText("ROZBRÓJ (DISARM)")
            self.arm_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        else:
            self.arm_button.setText("UZBRÓJ (ARM)")
            self.arm_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")

        self.update()  # Wywołuje paintEvent

    def paintEvent(self, event):
        # obliczamy moc silników
        self.calculate_motor_powers()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        scale = 2  # 1 cm = 2 px

        # Rysujemy tło (dla lepszego kontrastu przycisku, opcjonalne)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))

        # Rysujemy pojazd jako prostokąt
        painter.setBrush(QColor("gray"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(center_x - 10, center_y - 20, 20, 40)

        # Silniki – azymuty: 0 (prawo), 90 (góra), 180 (lewo), 270 (dół)
        motor_positions = {
            0: (center_x + 25, center_y),
            90: (center_x, center_y - 35),
            180: (center_x - 25, center_y),
            270: (center_x, center_y + 35),
        }

        motor_radius = 10

        # rysujemy silniki
        for direction, (x, y) in motor_positions.items():
            power = self.motor_powers.get(direction, 0)
            color = QColor("green") if power > 0 else QColor("red")

            # Okrąg
            painter.setBrush(color)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawEllipse(x - motor_radius, y - motor_radius, 2 * motor_radius, 2 * motor_radius)

            # Etykieta z mocą
            painter.setPen(Qt.GlobalColor.white)
            if direction == 0:  # prawo
                text_x = x + motor_radius + 5
                text_y = y + 5
            elif direction == 180:  # lewo
                text_x = x - motor_radius - 30
                text_y = y + 5
            elif direction == 90:  # góra
                text_x = x - 10
                text_y = y - motor_radius - 5
            elif direction == 270:  # dół
                text_x = x - 10
                text_y = y + motor_radius + 15
            else:
                text_x = x + 12
                text_y = y + 5

            painter.drawText(text_x, text_y, f"{int(power)}%")

        # Rysujemy linie dla każdego pomiaru
        pen = QPen(QColor("red"))
        pen.setWidth(2)
        painter.setPen(pen)

        self.obstacle_threshold_critical = 50  # w cm
        self.obstacle_threshold = 100  # w cm

        for direction, distance in self.ros_node.readings.items():
            angle_rad = math.radians(direction)
            dx = math.cos(angle_rad) * distance * scale
            dy = -math.sin(angle_rad) * distance * scale  # "-" bo oś Y w GUI jest odwrotna

            # Zmieniamy kolor linii jeśli przeszkoda jest blisko
            if distance < self.obstacle_threshold_critical:
                pen.setColor(QColor("red"))
            elif distance < self.obstacle_threshold:
                pen.setColor(QColor("yellow"))
            else:
                pen.setColor(QColor("green"))

            painter.setPen(pen)
            end_x = int(center_x + dx)
            end_y = int(center_y + dy)

            painter.drawLine(center_x, center_y, end_x, end_y)
            painter.setPen(QColor("white"))
            painter.drawText(end_x, end_y, f"{distance:.2f} cm")

        # Legenda w prawym dolnym rogu
        legend_x = self.width() - 270
        legend_y = self.height() - 100
        legend_spacing = 20

        legend_items = [
            ("< 0.5 m - STREFA KRYTYCZNA", QColor("red")),
            ("0.5–1.0 m - STREFA OSTRZEG.", QColor("orange")),
            (">= 1.0 m - STREFA BEZPIECZNA", QColor("green")),
        ]

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(legend_x, legend_y - 20, "LEGENDA:")

        for i, (text, color) in enumerate(legend_items):
            y = legend_y + i * legend_spacing
            painter.setBrush(color)
            painter.drawRect(legend_x, y, 15, 15)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(legend_x + 20, y + 12, text)

        # Tabela odczytów w lewym górnym rogu
        table_x = 20
        table_y = 40
        row_height = 20

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(table_x, table_y - 20, "AKTUALNE ODCZYTY CZUJNIKÓW:")

        sorted_readings = sorted(self.ros_node.readings.items())  # Sortuj po azymucie
        for i, (direction, distance) in enumerate(sorted_readings):
            text = f"Azymut: {direction}°   Odległość: {distance:.2f} cm"
            painter.drawText(table_x, table_y + i * row_height, text)

    def calculate_motor_powers(self):
        """
        Wylicza moc każdego z 4 silników (azymuty 0, 90, 180, 270)
        na podstawie aktualnych odczytów z czujników.
        """
        # Reset mocy silników
        motor_power = {0: 0.0, 90: 0.0, 180: 0.0, 270: 0.0}

        for direction, distance in self.ros_node.readings.items():
            if distance > 100:
                continue  # tylko reagujemy na bliskie przeszkody

            # Znajdujemy dwa najbliższe silniki
            for motor_dir in motor_power.keys():
                # Obliczamy różnicę kątów (w stopniach, cyklicznie)
                diff = abs((direction - motor_dir + 180) % 360 - 180)

                if diff <= 90:
                    # Silniki w zakresie 90° dostają udział mocy
                    # Im mniejsza różnica kątów, tym większy udział
                    weight = (90 - diff) / 90.0
                    # Im bliżej przeszkoda, tym większa moc (maks. 100%)
                    strength = max(0.0, 100 - distance)
                    motor_power[motor_dir] += weight * strength

        # kompensujemy siłę przeciwstawnych silników
        opposite_pairs = [(0, 180), (90, 270)]
        for a, b in opposite_pairs:
            if motor_power[a] < motor_power[b]:
                motor_power[b] = max(0.0, motor_power[b] - motor_power[a])
                motor_power[a] = 0.0
            elif motor_power[b] < motor_power[a]:
                motor_power[a] = max(0.0, motor_power[a] - motor_power[b])
                motor_power[b] = 0.0
            else:
                motor_power[a] = 0.0
                motor_power[b] = 0.0

        force_lateral = 0
        force_longitudinal = 0

        # Ogranicz do 100%
        for k in motor_power:
            motor_power[k] = round(min(100, motor_power[k]), 2)
            if motor_power[k] > 0:
                if k == 0:
                    force_lateral = 0 - motor_power[k]
                elif k == 180:
                    force_lateral = motor_power[k]
                elif k == 90:
                    force_longitudinal = 0 - motor_power[k]
                elif k == 270:
                    force_longitudinal = motor_power[k]

        self.motor_powers = motor_power

        # Format: [Silnik_Główny, Silnik_Boczny]
        self.ros_node.publish_motor_commands(force_longitudinal, force_lateral)


def main(args=None):
    rclpy.init(args=args)

    try:
        motor_subscriber = MotorSubscriber()

        app = QApplication(sys.argv)
        gui = DistanceGUI(motor_subscriber)
        gui.show()

        # Timer do ROS2 spin_once
        ros_timer = QTimer()
        ros_timer.timeout.connect(lambda: rclpy.spin_once(motor_subscriber, timeout_sec=0.01))
        ros_timer.start(10)

        app.exec()

    finally:
        motor_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

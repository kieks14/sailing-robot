import random

class SampleDataGenerator:
    def __init__(self):
        # Initialize boat data parameters (you can customize these)
        self.heading = 0.0  # Boat's heading in degrees (0-360)
        self.wind_direction_true = 0.0  # True wind direction in degrees (0-360)
        self.wind_speed_true = 5.0  # True wind speed in knots
        self.boat_speed = 3.0  # Boat speed in knots
        self.sailing_state = "normal"  # Boat's current sailing state (e.g., "normal", "switch_to_port_tack", etc.)

    def generate_sample_data(self):
        # Simulate changes in boat data (for testing purposes)
        self.heading += random.uniform(-2.0, 2.0)  # Simulate small heading changes
        self.heading %= 360.0

        self.wind_direction_true += random.uniform(-2.0, 2.0)  # Simulate wind direction changes
        self.wind_direction_true %= 360.0

        self.wind_speed_true += random.uniform(-0.5, 0.5)  # Simulate small wind speed changes
        self.wind_speed_true = max(0.0, self.wind_speed_true)  # Ensure wind speed is non-negative

        self.boat_speed += random.uniform(-0.2, 0.2)  # Simulate small boat speed changes
        self.boat_speed = max(0.0, self.boat_speed)  # Ensure boat speed is non-negative

        # Create a dictionary to represent the boat's current state
        boat_data = {
            "heading": self.heading,
            "wind_direction_true": self.wind_direction_true,
            "wind_speed_true": self.wind_speed_true,
            "boat_speed": self.boat_speed,
        }

        return boat_data

if __name__ == "__main__":
    # Create a SampleDataGenerator instance
    data_generator = SampleDataGenerator()

    # Simulate boat data for a specified number of iterations
    num_iterations = 10
    for _ in range(num_iterations):
        boat_data = data_generator.generate_sample_data()
        print("Boat Data:")
        print("Heading:", boat_data["heading"])
        print("Wind Direction:", boat_data["wind_direction_true"])
        print("Wind Speed:", boat_data["wind_speed_true"])
        print("Boat Speed:", boat_data["boat_speed"])

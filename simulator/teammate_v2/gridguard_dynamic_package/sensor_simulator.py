from collections import deque
import random
import numpy as np

WINDOW_SIZE = 60
FEATURES = ["I", "V", "T", "a"]


class SensorSimulator:
    """Synthetic sensor simulator for UI/integration testing only."""

    ALLOWED_FAULTS = {"overload", "overheating", "vibration", "voltage_sag"}

    def __init__(self, asset_id, seed=None):
        self.asset_id = asset_id
        self.rng = random.Random(seed)
        self.history = deque(maxlen=WINDOW_SIZE)
        self.load_factor = 0.75
        self.fault = None
        self.temperature = 35.0
        self.vibration = 1.0
        self.last_reading = None

    def set_load(self, factor):
        factor = float(factor)
        if not 0.1 <= factor <= 1.5:
            raise ValueError("Load must be between 0.1 and 1.5")
        self.load_factor = factor

    def inject_fault(self, fault="overload"):
        if fault not in self.ALLOWED_FAULTS:
            raise ValueError(f"Fault must be one of: {sorted(self.ALLOWED_FAULTS)}")
        self.fault = fault

    def clear_fault(self):
        self.fault = None

    def reset(self):
        self.history.clear()
        self.load_factor = 0.75
        self.fault = None
        self.temperature = 35.0
        self.vibration = 1.0
        self.last_reading = None

    def step(self):
        load = self.load_factor

        current = 8.0 * load + self.rng.gauss(0, 0.15)
        voltage = 11.0 + self.rng.gauss(0, 0.04)
        heat_target = 30.0 + 35.0 * load**2

        if self.fault == "overload":
            current *= 1.35
            heat_target += 12.0
        elif self.fault == "overheating":
            heat_target += 25.0
        elif self.fault == "voltage_sag":
            voltage -= 0.8

        vibration_target = 5.0 if self.fault == "vibration" else 0.8 + 1.2 * load

        # Smooth response: readings approach targets over multiple ticks.
        self.temperature += 0.12 * (heat_target - self.temperature) + self.rng.gauss(0, 0.15)
        self.vibration += 0.25 * (vibration_target - self.vibration) + self.rng.gauss(0, 0.08)

        current = max(0.0, current)
        voltage = max(0.0, voltage)
        vibration = max(0.0, self.vibration)

        reading = {
            "asset_id": self.asset_id,
            "current_A": round(current, 3),
            "voltage_kV": round(voltage, 3),
            "temperature_C": round(self.temperature, 2),
            "vibration_mm_s": round(vibration, 3),
            "load_factor": round(load, 2),
            "fault_scenario": self.fault or "none",
        }

        self.history.append([current, voltage, self.temperature, vibration])
        self.last_reading = reading
        return reading

    def get_window(self):
        """Return shape (1, 60, 4) after 60 samples; otherwise None."""
        if len(self.history) < WINDOW_SIZE:
            return None
        return np.asarray(self.history, dtype=np.float32).reshape(1, WINDOW_SIZE, 4)

import os
import sys

MCL_DLL_PATH    = r"C:\Program Files\Mad City Labs\MicroDrive\API"
MCL_PYTHON_PATH = r"C:\Program Files\Mad City Labs\MicroDrive\API\Python"

# Add DLL and Python wrapper to search paths
os.add_dll_directory(MCL_DLL_PATH)
sys.path.insert(0, MCL_PYTHON_PATH)

from MCL_MicroDrive_Wrapper import MCL_Microdrive, MCL_MD_Exceptions  # noqa: E402


class MCLMicrostage:
    """Thin convenience wrapper around MCL_Microdrive.

    Provides absolute-position semantics on top of the relative-move API.
    Positions are tracked via the hardware encoders (mm).

    axis_x / axis_y: MCL axis numbers (M1=1 … M6=6) mapped to X and Y.
    encoder_x / encoder_y: encoder indices (0-based) mapped to X and Y.
    """

    def __init__(self, serial_num=None, debug=False,
                 axis_x=1, axis_y=2,
                 encoder_x=0, encoder_y=1,
                 invert_x=False, invert_y=False):
        self.debug = debug
        self.axis_x = axis_x
        self.axis_y = axis_y
        self.encoder_x = encoder_x
        self.encoder_y = encoder_y
        self.invert_x = invert_x
        self.invert_y = invert_y

        self._dev = MCL_Microdrive()

        if serial_num is not None:
            self._dev.grab_all_handles()
            self.handle = self._dev.get_handle_by_serial(serial_num)
        else:
            self.handle = self._dev.init_handle()

        axis_bitmap = self._dev.get_axis_info(self.handle)
        if self.debug:
            print(f"MCLMicrostage available axes (bitmap): {axis_bitmap}")

        # Query velocity range per axis
        def _axis_vel_range(axis):
            try:
                _, _, max_v, _, _, min_v, _ = self._dev.axis_information(axis, self.handle)
                return (min_v if min_v > 0 else 0.001, max_v)
            except Exception:
                return (0.001, 10.0)

        self._x_min_vel, self._x_max_vel = _axis_vel_range(self.axis_x)
        self._y_min_vel, self._y_max_vel = _axis_vel_range(self.axis_y)

        self.min_velocity = min(self._x_min_vel, self._y_min_vel)
        self.max_velocity = min(self._x_max_vel, self._y_max_vel)
        self._default_velocity = self.max_velocity / 2.0

        if self.debug:
            print(f"MCLMicrostage axis {self.axis_x} (X): vel [{self._x_min_vel:.4f}, {self._x_max_vel:.4f}] mm/s")
            print(f"MCLMicrostage axis {self.axis_y} (Y): vel [{self._y_min_vel:.4f}, {self._y_max_vel:.4f}] mm/s")

    # ------------------------------------------------------------------
    # Position reading
    # ------------------------------------------------------------------

    def read_encoders(self):
        """Return all encoder positions in mm as a list."""
        return self._dev.read_encoders(self.handle)

    def read_pos_x(self):
        raw = self.read_encoders()[self.encoder_x]
        return -raw if self.invert_x else raw

    def read_pos_y(self):
        raw = self.read_encoders()[self.encoder_y]
        return -raw if self.invert_y else raw

    # ------------------------------------------------------------------
    # Relative moves (non-blocking)
    # ------------------------------------------------------------------

    def _clamp(self, velocity, min_v, max_v):
        v = velocity if velocity is not None else self._default_velocity
        return max(min_v, min(max_v, v))

    def move_rel_x(self, delta_mm, velocity=None):
        if self.is_moving():
            return
        v = self._clamp(velocity, self._x_min_vel, self._x_max_vel)
        physical_delta = -delta_mm if self.invert_x else delta_mm
        self._dev.move(self.axis_x, v, physical_delta, self.handle)

    def move_rel_y(self, delta_mm, velocity=None):
        if self.is_moving():
            return
        v = self._clamp(velocity, self._y_min_vel, self._y_max_vel)
        physical_delta = -delta_mm if self.invert_y else delta_mm
        self._dev.move(self.axis_y, v, physical_delta, self.handle)

    # ------------------------------------------------------------------
    # Absolute moves (non-blocking)
    # ------------------------------------------------------------------

    def move_x(self, target_mm, velocity=None):
        if self.is_moving():
            return
        current = self.read_pos_x()
        delta = target_mm - current
        if abs(delta) > 1e-6:
            self.move_rel_x(delta, velocity)

    def move_y(self, target_mm, velocity=None):
        if self.is_moving():
            return
        current = self.read_pos_y()
        delta = target_mm - current
        if abs(delta) > 1e-6:
            self.move_rel_y(delta, velocity)

    # ------------------------------------------------------------------
    # Status / control
    # ------------------------------------------------------------------

    def is_moving(self):
        return bool(self._dev.move_status(self.handle))

    def stop(self):
        return self._dev.stop(self.handle)

    def wait(self):
        self._dev.wait(self.handle)

    def reset_encoders(self):
        return self._dev.reset_encoders(self.handle)

    # ------------------------------------------------------------------
    # Limit switch status
    # MCL convention: bit (2*(N-1)) = MN LS1, bit (2*(N-1)+1) = MN LS2
    # Bit = 1 → limit NOT reached; bit = 0 → AT limit
    # ------------------------------------------------------------------

    def read_status(self):
        """Return raw status unsigned short."""
        return self._dev.status(self.handle)

    def _limit_mask(self, axis):
        b = (axis - 1) * 2
        return (1 << b) | (1 << (b + 1))

    def is_at_any_limit(self):
        status = self.read_status()
        mask = self._limit_mask(self.axis_x) | self._limit_mask(self.axis_y)
        return (status & mask) != mask

    def is_at_limit_x_neg(self):
        bit = (self.axis_x - 1) * 2
        return not bool(self.read_status() & (1 << bit))

    def is_at_limit_x_pos(self):
        bit = (self.axis_x - 1) * 2 + 1
        return not bool(self.read_status() & (1 << bit))

    def is_at_limit_y_neg(self):
        bit = (self.axis_y - 1) * 2
        return not bool(self.read_status() & (1 << bit))

    def is_at_limit_y_pos(self):
        bit = (self.axis_y - 1) * 2 + 1
        return not bool(self.read_status() & (1 << bit))

    def get_serial_number(self):
        return self._dev.get_serial_number(self.handle)

    def close(self):
        self._dev.release_handle(self.handle)

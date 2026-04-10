import time
from ScopeFoundry import Measurement
from qtpy import QtWidgets


CAL_VELOCITY = 0.5  # mm/s — slow, safe speed for limit finding
LARGE_MOVE   = 50.0  # mm — larger than any possible travel range


class MCLMicrostageCalibration(Measurement):
    """Finds the travel limits of the MCL microstage by driving to each
    limit switch, recording the encoder position, then returning to centre.

    Stores results in hw.settings: x_min, x_max, y_min, y_max.
    """

    name = 'MCL_Microstage_Calibration'

    def __init__(self, app, name=None, hw_name='mcl_microstage'):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)

    def setup(self):
        self.hw = self.app.hardware[self.hw_name]

    def setup_figure(self):
        self.ui = QtWidgets.QLabel(
            "MCL Microstage Calibration\n\nDrives to each limit switch to find travel range.\nResults stored in hardware settings: x_min, x_max, y_min, y_max.")
        self.ui.setMargin(16)

    def run(self):
        stage = self.hw.stage
        v = CAL_VELOCITY

        self._find_x_limits(stage, v)
        if self.interrupt_measurement_called:
            return

        self._find_y_limits(stage, v)
        if self.interrupt_measurement_called:
            return

        # Move to centre of travel
        cx = (self.hw.settings['x_min'] + self.hw.settings['x_max']) / 2.0
        cy = (self.hw.settings['y_min'] + self.hw.settings['y_max']) / 2.0
        stage.move_rel_x(cx - stage.read_pos_x(), v)
        stage.wait()
        stage.move_rel_y(cy - stage.read_pos_y(), v)
        stage.wait()

    def _find_x_limits(self, stage, v):
        # Drive toward negative X limit
        stage._dev.move(stage.axis_x,
                        stage._clamp(v, stage._x_min_vel, stage._x_max_vel),
                        -LARGE_MOVE if not stage.invert_x else LARGE_MOVE,
                        stage.handle)
        self._wait_for_stop(stage)
        if self.interrupt_measurement_called:
            return

        # Zero encoder here — negative limit becomes 0
        stage._dev.reset_encoder(stage.axis_x, stage.handle)

        # Drive toward positive X limit
        stage._dev.move(stage.axis_x,
                        stage._clamp(v, stage._x_min_vel, stage._x_max_vel),
                        LARGE_MOVE if not stage.invert_x else -LARGE_MOVE,
                        stage.handle)
        self._wait_for_stop(stage)
        if self.interrupt_measurement_called:
            return

        self.hw.settings['x_min'] = 0.0
        self.hw.settings['x_max'] = abs(stage.read_pos_x())
        print(f"MCL calibration X: min=0.0000  max={self.hw.settings['x_max']:.4f} mm")

    def _find_y_limits(self, stage, v):
        # Drive toward negative Y limit
        stage._dev.move(stage.axis_y,
                        stage._clamp(v, stage._y_min_vel, stage._y_max_vel),
                        -LARGE_MOVE if not stage.invert_y else LARGE_MOVE,
                        stage.handle)
        self._wait_for_stop(stage)
        if self.interrupt_measurement_called:
            return

        # Zero encoder here — negative limit becomes 0
        stage._dev.reset_encoder(stage.axis_y, stage.handle)

        # Drive toward positive Y limit
        stage._dev.move(stage.axis_y,
                        stage._clamp(v, stage._y_min_vel, stage._y_max_vel),
                        LARGE_MOVE if not stage.invert_y else -LARGE_MOVE,
                        stage.handle)
        self._wait_for_stop(stage)
        if self.interrupt_measurement_called:
            return

        self.hw.settings['y_min'] = 0.0
        self.hw.settings['y_max'] = abs(stage.read_pos_y())
        print(f"MCL calibration Y: min=0.0000  max={self.hw.settings['y_max']:.4f} mm")

    def _wait_for_stop(self, stage):
        """Wait until the stage stops moving (hit limit or finished move)."""
        while stage.is_moving():
            if self.interrupt_measurement_called:
                stage.stop()
                return
            time.sleep(0.05)

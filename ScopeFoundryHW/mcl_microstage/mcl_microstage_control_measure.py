from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
from qtpy import QtCore

LARGE_MOVE = 50.0  # mm

LIMIT_ON  = "background-color:#e53935;color:white;font-weight:bold;border-radius:4px;padding:2px 6px;"
LIMIT_OFF = "background-color:#e0e0e0;color:#9e9e9e;font-weight:bold;border-radius:4px;padding:2px 6px;"
PBAR      = ("QProgressBar{min-height:22px;border:1px solid #aaa;border-radius:4px;"
             "text-align:center;font-weight:bold;}"
             "QProgressBar::chunk{background:#43a047;border-radius:3px;}")


class _CalibrationThread(QtCore.QThread):
    progress    = QtCore.Signal(int)
    status_msg  = QtCore.Signal(str)
    pos_updated = QtCore.Signal(float, float)

    def __init__(self, stage, hw_settings):
        super().__init__()
        self.stage = stage
        self.hw_settings = hw_settings
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True
        self.stage.stop()

    def run(self):
        s = self.stage

        self.status_msg.emit("Finding X negative limit...")
        self.progress.emit(10)
        s._dev.move(s.axis_x, s._clamp(s._x_max_vel, s._x_min_vel, s._x_max_vel),
                    -LARGE_MOVE if not s.invert_x else LARGE_MOVE, s.handle)
        self._wait(s)
        if self._stop_flag: self.status_msg.emit("Stopped"); return

        self.progress.emit(20)
        s._dev.reset_encoder(s.axis_x, s.handle)
        self.status_msg.emit("X zeroed at negative limit")
        self.progress.emit(30)

        self.status_msg.emit("Finding X positive limit...")
        self.progress.emit(40)
        s._dev.move(s.axis_x, s._clamp(s._x_max_vel, s._x_min_vel, s._x_max_vel),
                    LARGE_MOVE if not s.invert_x else -LARGE_MOVE, s.handle)
        self._wait(s)
        if self._stop_flag: self.status_msg.emit("Stopped"); return

        self.hw_settings['x_min'] = 0.0
        self.hw_settings['x_max'] = abs(s.read_pos_x())
        self.progress.emit(50)

        self.status_msg.emit("Finding Y negative limit...")
        self.progress.emit(60)
        s._dev.move(s.axis_y, s._clamp(s._y_max_vel, s._y_min_vel, s._y_max_vel),
                    -LARGE_MOVE if not s.invert_y else LARGE_MOVE, s.handle)
        self._wait(s)
        if self._stop_flag: self.status_msg.emit("Stopped"); return

        self.progress.emit(70)
        s._dev.reset_encoder(s.axis_y, s.handle)
        self.status_msg.emit("Y zeroed at negative limit")
        self.progress.emit(80)

        self.status_msg.emit("Finding Y positive limit...")
        self.progress.emit(90)
        s._dev.move(s.axis_y, s._clamp(s._y_max_vel, s._y_min_vel, s._y_max_vel),
                    LARGE_MOVE if not s.invert_y else -LARGE_MOVE, s.handle)
        self._wait(s)
        if self._stop_flag: self.status_msg.emit("Stopped"); return

        self.hw_settings['y_min'] = 0.0
        self.hw_settings['y_max'] = abs(s.read_pos_y())
        self.progress.emit(100)
        self.status_msg.emit(
            f"Done — X: 0→{self.hw_settings['x_max']:.3f} mm  "
            f"Y: 0→{self.hw_settings['y_max']:.3f} mm")

    def _wait(self, stage):
        while stage.is_moving() and not self._stop_flag:
            try:
                self.pos_updated.emit(stage.read_pos_x(), stage.read_pos_y())
            except Exception:
                pass
            self.msleep(200)


class MCLMicrostageControlMeasure(Measurement):

    name = 'MCL_Microstage_Control'

    def __init__(self, app, name=None, hw_name='mcl_microstage'):
        self.hw_name = hw_name
        Measurement.__init__(self, app, name=name)

    def setup(self):
        self.settings.New('jog_step_xy', dtype=float, unit='mm',
                          initial=0.1, spinbox_decimals=4)
        self.stage = self.app.hardware[self.hw_name]
        self._cal_thread = None

    def setup_figure(self):
        self.ui = load_qt_ui_file(sibling_path(__file__, 'mcl_microstage_control.ui'))

        self.stage.settings.connected.connect_to_widget(self.ui.mcl_connect_checkBox)
        self.stage.settings.x_position.connect_to_widget(self.ui.x_pos_doubleSpinBox)
        self.stage.settings.y_position.connect_to_widget(self.ui.y_pos_doubleSpinBox)
        self.settings.jog_step_xy.connect_to_widget(self.ui.xy_step_doubleSpinBox)
        self.stage.settings.velocity.connect_to_widget(self.ui.velocity_doubleSpinBox)

        self.ui.x_target_lineEdit.returnPressed.connect(
            self.stage.settings.x_target.update_value)
        self.ui.x_target_lineEdit.returnPressed.connect(
            lambda: self.ui.x_target_lineEdit.clear())
        self.ui.y_target_lineEdit.returnPressed.connect(
            self.stage.settings.y_target.update_value)
        self.ui.y_target_lineEdit.returnPressed.connect(
            lambda: self.ui.y_target_lineEdit.clear())

        self.ui.x_up_pushButton.clicked.connect(self.x_up)
        self.ui.x_down_pushButton.clicked.connect(self.x_down)
        self.ui.y_up_pushButton.clicked.connect(self.y_up)
        self.ui.y_down_pushButton.clicked.connect(self.y_down)
        self.ui.stop_pushButton.clicked.connect(self.stage.stop)
        self.ui.reset_encoders_pushButton.clicked.connect(self.stage.reset_encoders)

        self.ui.calibrate_pushButton.clicked.connect(self._start_calibration)
        self.ui.stop_cal_pushButton.clicked.connect(self._stop_calibration)

        self.ui.cal_progressBar.setStyleSheet(PBAR)

        self.ui.limit_indicator_label.setStyleSheet(LIMIT_OFF)
        self._flash_state = False
        self._flash_timer = QtCore.QTimer()
        self._flash_timer.setInterval(400)
        self._flash_timer.timeout.connect(self._on_flash)
        self.stage.settings.at_limit.updated_value.connect(self._on_at_limit)

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def _jog_widgets(self):
        return [self.ui.x_up_pushButton, self.ui.x_down_pushButton,
                self.ui.y_up_pushButton, self.ui.y_down_pushButton,
                self.ui.x_target_lineEdit, self.ui.y_target_lineEdit,
                self.ui.stop_pushButton, self.ui.reset_encoders_pushButton,
                self.ui.calibrate_pushButton]

    def _start_calibration(self):
        if not self.stage.settings['connected']:
            return
        for w in self._jog_widgets():
            w.setEnabled(False)
        self.ui.stop_cal_pushButton.setEnabled(True)
        self.ui.cal_progressBar.setValue(0)
        self.ui.cal_status_label.setText("Starting...")

        self._cal_thread = _CalibrationThread(self.stage.stage, self.stage.settings)
        self._cal_thread.progress.connect(self.ui.cal_progressBar.setValue)
        self._cal_thread.status_msg.connect(self.ui.cal_status_label.setText)
        self._cal_thread.pos_updated.connect(self._on_cal_pos)
        self._cal_thread.finished.connect(self._on_cal_done)
        self._cal_thread.start()

    def _stop_calibration(self):
        if self._cal_thread and self._cal_thread.isRunning():
            self._cal_thread.stop()

    def _on_cal_done(self):
        for w in self._jog_widgets():
            w.setEnabled(True)
        self.ui.stop_cal_pushButton.setEnabled(False)

    def _on_cal_pos(self, x, y):
        self.ui.x_pos_doubleSpinBox.setValue(x)
        self.ui.y_pos_doubleSpinBox.setValue(y)

    # ------------------------------------------------------------------
    # Limit indicator
    # ------------------------------------------------------------------

    def _on_at_limit(self, at_limit):
        if at_limit:
            self._flash_timer.start()
        else:
            self._flash_timer.stop()
            self.ui.limit_indicator_label.setStyleSheet(LIMIT_OFF)

    def _on_flash(self):
        self._flash_state = not self._flash_state
        self.ui.limit_indicator_label.setStyleSheet(
            LIMIT_ON if self._flash_state else LIMIT_OFF)

    # ------------------------------------------------------------------
    # Jog
    # ------------------------------------------------------------------

    def x_up(self):   self.stage.settings['x_target'] += self.settings['jog_step_xy']
    def x_down(self): self.stage.settings['x_target'] -= self.settings['jog_step_xy']
    def y_up(self):   self.stage.settings['y_target'] += self.settings['jog_step_xy']
    def y_down(self): self.stage.settings['y_target'] -= self.settings['jog_step_xy']

    def run(self): pass

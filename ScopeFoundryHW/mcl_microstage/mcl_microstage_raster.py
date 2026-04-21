from ScopeFoundry.scanning import BaseRaster2DSlowScan
import time

class MCLMicrostage2DScan(BaseRaster2DSlowScan):

    name = 'mcl_microstage_raster'

    def __init__(self, app):
        BaseRaster2DSlowScan.__init__(self, app,
                                      h_limits=(0, 25), v_limits=(0, 25),
                                      h_spinbox_step = 0.010, v_spinbox_step=0.010,
                                      h_unit="mm", v_unit="mm", circ_roi_size=0.05)

    def setup(self):
        self.settings.New('debug', dtype=bool, initial=False)
        BaseRaster2DSlowScan.setup(self)
        self.stage = self.app.hardware['mcl_microstage']

    def new_pt_pos(self, x, y):
        # overwrite the function that lets you drag and drop the position
        if not self.stage.settings['connected']:
            return

        self.stage.settings["x_target"] = x
        self.stage.settings["y_target"] = y
        while self.stage.is_busy_xy():
            time.sleep(0.01)
        self.stage.correct_backlash(0.01)

    def move_position_start(self, h, v):
        if self.settings['debug']:
            print(f'{self.name} start scan, moving to x={h:.4f}, y={v:.4f}')
        self.stage.settings["x_target"] = h
        self.stage.settings["y_target"] = v
        while self.stage.is_busy_xy():
            time.sleep(0.01)
        self.stage.correct_backlash(0.01)

    def move_position_slow(self, h, v, dh, dv):
        if self.settings['debug']:
            print(f'{self.name} new line, moving to x={h:.4f}, y={v:.4f}')
        # Backlash correction integrated into the line start
        self.stage.settings["x_target"] = h - 0.01
        self.stage.settings["y_target"] = v
        while self.stage.is_busy_xy():
            time.sleep(0.01)
        self.stage.settings["x_target"] = h
        while self.stage.is_busy_xy():
            time.sleep(0.01)

    def move_position_fast(self, h, v, dh, dv):
        # move without explicitly waiting for stage to finish
        self.stage.settings["x_target"] = h
        # Wait based on velocity
        wait_time = 1.1 * abs(dh) / self.stage.settings['velocity']
        time.sleep(max(0.001, wait_time))

class MCLMicrostageDelay2DScan(MCLMicrostage2DScan):

    name = 'mcl_microstage_delay_raster'

    def setup_figure(self):
        MCLMicrostage2DScan.setup_figure(self)
        self.set_details_widget(
            widget=self.settings.New_UI(include=['pixel_time', 'frame_time']))

    def scan_specific_setup(self):
        self.settings.pixel_time.change_readonly(False)

    def collect_pixel(self, pixel_num, k, j, i):
        time.sleep(self.settings['pixel_time'])

    def update_display(self):
        pass

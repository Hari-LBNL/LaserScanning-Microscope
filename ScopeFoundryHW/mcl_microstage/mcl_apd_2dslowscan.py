from ScopeFoundryHW.mcl_microstage.mcl_microstage_raster import MCLMicrostage2DScan
import numpy as np
import time

class MCL_APD_2Dslowscan(MCLMicrostage2DScan):

    name = 'MCL_APD_2Dslowscan'

    def __init__(self, app):
        MCLMicrostage2DScan.__init__(self, app)

    def setup(self):
        MCLMicrostage2DScan.setup(self)

    def pre_scan_setup(self):
        # Hardware
        self.ph_hw = self.app.hardware['picoharp']
        self.ph_count_rate = self.ph_hw.settings.count_rate0

        # Scan specific setup

        # Create data arrays
        self.count_rate_map = np.zeros(self.scan_shape, dtype=float)
        if self.settings['save_h5']:
            self.count_rate_map_h5 = self.h5_meas_group.create_dataset('count_rate_map',
                                                                       shape=self.scan_shape,
                                                                       dtype=float,
                                                                       compression='gzip')

    def collect_pixel(self, pixel_num, k, j, i):
        # Collect data
        # Wait for the acquisition time set in PicoHarp
        time.sleep(self.ph_hw.settings['Tacq'])
        self.ph_count_rate.read_from_hardware()
        val = self.ph_count_rate.val

        # Store in arrays
        self.count_rate_map[k,j,i] = val
        if self.settings['save_h5']:
            self.count_rate_map_h5[k,j,i] = val

        self.display_image_map[k,j,i] = val

import numpy as np
import time
from .mcl_microstage_raster import MCLMicrostage2DScan
from ScopeFoundryHW.andor_camera.andor_ccd_readout import AndorCCDReadoutMeasure

class MCLAndorHyperSpec2DScan(MCLMicrostage2DScan):

    name = "mcl_andor_hyperspec_scan"

    def __init__(self, app):
        MCLMicrostage2DScan.__init__(self, app)

    def setup(self):
        MCLMicrostage2DScan.setup(self)

    def scan_specific_setup(self):
        MCLMicrostage2DScan.scan_specific_setup(self)
        # Hardware components are already available in self.app.hardware
        # But we need the readout measurement to trigger acquisitions
        self.andor_ccd_readout = self.app.measurements['andor_ccd_readout']

        # We can add a custom UI here if needed, mirroring the template
        # For now, let's keep it simple and use the base class UI

    def pre_scan_setup(self):
        # Prepare Andor CCD for scan
        self.andor_ccd_readout.settings['acquire_bg'] = False
        self.andor_ccd_readout.settings['continuous'] = False
        self.andor_ccd_readout.settings['save_h5'] = False

        # Prepare stage
        time.sleep(0.01)
        # self.stage is set in MCLMicrostage2DScan.setup()

    def collect_pixel(self, pixel_num, k, j, i):
        if self.settings['debug']:
            print(f"collect_pixel {pixel_num} (k={k}, j={j}, i={i})")

        # Trigger Andor CCD acquisition
        self.andor_ccd_readout.interrupt_measurement_called = self.interrupt_measurement_called
        self.andor_ccd_readout.run()

        if pixel_num == 0:
            self.log.info("pixel 0: creating data arrays")
            # spectra_data is assumed to be the attribute where AndorCCDReadoutMeasure stores the latest spectrum
            # Based on the template: self.andor_ccd_readout.spectra_data
            spec_sample = self.andor_ccd_readout.spectra_data
            spec_map_shape = self.scan_shape + spec_sample.shape

            self.spec_map = np.zeros(spec_map_shape, dtype=float)

            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset(
                                     'spec_map', spec_map_shape, dtype=float)
            else:
                self.spec_map_h5 = np.zeros(spec_map_shape)

            # Store wavelengths if available
            if hasattr(self.andor_ccd_readout, 'wls'):
                self.wls = np.array(self.andor_ccd_readout.wls)
                if self.settings['save_h5']:
                    self.h5_meas_group['wls'] = self.wls

        # Store the spectrum
        spec = self.andor_ccd_readout.spectra_data
        self.spec_map[k, j, i, :] = spec
        if self.settings['save_h5']:
            self.spec_map_h5[k, j, i, :] = spec

        # Update display image (sum of spectrum for intensity map)
        self.display_image_map[k, j, i] = spec.sum()

    def post_scan_cleanup(self):
        # Restore Andor CCD settings if needed
        self.andor_ccd_readout.settings['save_h5'] = True

    def update_display(self):
        MCLMicrostage2DScan.update_display(self)
        self.andor_ccd_readout.update_display()

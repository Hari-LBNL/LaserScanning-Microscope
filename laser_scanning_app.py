from ScopeFoundry import BaseMicroscopeApp



"""
Harishankar Jayakumar 4/3/26 
"""

class LaserScanningApp(BaseMicroscopeApp):


    name = 'laser_scanning_app'

    def setup(self):

        from ScopeFoundryHW.mcp_server.mcp_server_hw import MCPServerHardware
        self.add_hardware(MCPServerHardware(self))

        from ScopeFoundryHW.session_manager.git_session_manager_hw import GitSessionManagerHW
        self.add_hardware(GitSessionManagerHW)

        from ScopeFoundryHW.mcl_microstage.mcl_microstage_hw import MCLMicrostageHW
        self.add_hardware(MCLMicrostageHW(self))
        from ScopeFoundryHW.mcl_microstage.mcl_microstage_control_measure import MCLMicrostageControlMeasure
        self.add_measurement(MCLMicrostageControlMeasure(self))

        from ScopeFoundryHW.toupcam import  ToupCamHW, ToupCamLiveMeasure
        self.add_hardware(ToupCamHW(self))
        self.add_measurement(ToupCamLiveMeasure(self))

        #from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
        #asi_stage = self.add_hardware(ASIStageHW(self,invert_x=True, invert_y = True,enable_z=True))
        #from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
        #asi_control = self.add_measurement(ASIStageControlMeasure(self))

        from ScopeFoundryHW.acton_spec.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))

        from ScopeFoundryHW.andor_camera.andor_ccd import AndorCCDHW
        self.add_hardware(AndorCCDHW(self))

        from ScopeFoundryHW.andor_camera.andor_ccd_readout import AndorCCDReadoutMeasure
        self.add_measurement(AndorCCDReadoutMeasure(self))

        from ScopeFoundryHW.picoharp.picoharp import PicoHarpHW
        self.add_hardware(PicoHarpHW(self))
        #from ScopeFoundryHW.andor_camera.andor_ccd_kinetic_measure import AndorCCDKineticMeasure
        #self.add_measurement(AndorCCDKineticMeasure(self))

        #from ScopeFoundryHW.mcl_microstage.mcl_microstage_raster import MCLMicrostage2DScan, MCLMicrostageDelay2DScan
        #self.add_measurement(MCLMicrostage2DScan(self))
        #self.add_measurement(MCLMicrostageDelay2DScan(self))

        from ScopeFoundryHW.mcl_microstage.mcl_andor_hyperspec_raster import MCLAndorHyperSpec2DScan
        self.add_measurement(MCLAndorHyperSpec2DScan(self))

        from ScopeFoundryHW.mcl_microstage.mcl_apd_2dslowscan import MCL_APD_2Dslowscan
        self.add_measurement(MCL_APD_2Dslowscan(self))

        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from ScopeFoundryHW.apd_counter.measure.apd_optimizer import APDOptimizerMeasurement
        self.add_measurement_component(APDOptimizerMeasurement(self))



        



if __name__ == "__main__":
    import sys
    app = LaserScanningApp(sys.argv)
    app.exec_()

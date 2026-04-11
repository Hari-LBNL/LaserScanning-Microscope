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

        from ScopeFoundryHW.asi_stage.asi_stage_hw import ASIStageHW
        asi_stage = self.add_hardware(ASIStageHW(self,invert_x=True, invert_y = True,enable_z=True))
        from ScopeFoundryHW.asi_stage.asi_stage_control_measure import ASIStageControlMeasure
        asi_control = self.add_measurement(ASIStageControlMeasure(self))

        from ScopeFoundryHW.acton_spec.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))

        from ScopeFoundryHW.andor_camera.andor_ccd import AndorCCDHW
        self.add_hardware(AndorCCDHW(self))


        



if __name__ == "__main__":
    import sys
    app = LaserScanningApp(sys.argv)
    app.exec_()

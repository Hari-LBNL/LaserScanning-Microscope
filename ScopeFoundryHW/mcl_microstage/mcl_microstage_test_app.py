"""Minimal test app for the MCL MicroDrive microstage hardware component."""
import sys
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.mcl_microstage.mcl_microstage_hw import MCLMicrostageHW


class MCLMicrostageTestApp(BaseMicroscopeApp):
    name = 'mcl_microstage_test_app'

    def setup(self):
        self.add_hardware(MCLMicrostageHW(self))


if __name__ == '__main__':
    app = MCLMicrostageTestApp(sys.argv)
    app.exec_()

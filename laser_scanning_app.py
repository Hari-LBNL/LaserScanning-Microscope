from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.mcp_server.mcp_server_hw import MCPServerHardware
from ScopeFoundryHW.session_manager.git_session_manager_hw import GitSessionManagerHW

"""
Harishankar Jayakumar 4/3/26 
"""

class LaserScanningApp(BaseMicroscopeApp):


    name = 'laser_scanning_app'

    def setup(self):


        self.add_hardware_component(MCPServerHardware(self))


        self.add_hardware(GitSessionManagerHW)


        



if __name__ == "__main__":
    import sys
    app = LaserScanningApp(sys.argv)
    app.exec_()

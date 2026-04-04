from ScopeFoundry import BaseMicroscopeApp

class LaserScanningApp(BaseMicroscopeApp):
        print("Hello from laserscanning-microscope!")


if __name__ == "__main__":
    import sys
    app = LaserScanningApp(sys.argv)
    app.exec_()

from ScopeFoundry import HardwareComponent
from qtpy import QtCore

from .mcl_microstage_dev import MCLMicrostage


class MCLMicrostageHW(HardwareComponent):

    name = 'mcl_microstage'

    def __init__(self, app, debug=False, name=None,
                 enable_x=True, enable_y=True, enable_z=False):
        self.enable_x = enable_x
        self.enable_y = enable_y
        self.enable_z = enable_z
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        pos_kwargs = dict(initial=0.0, dtype=float, unit='mm',
                          spinbox_decimals=4, spinbox_step=0.1)

        if self.enable_x:
            self.settings.New('x_position', ro=True, **pos_kwargs)
            self.settings.New('x_target',   ro=False, **pos_kwargs)

        if self.enable_y:
            self.settings.New('y_position', ro=True, **pos_kwargs)
            self.settings.New('y_target',   ro=False, **pos_kwargs)

        if self.enable_z:
            self.settings.New('z_position', ro=True, **pos_kwargs)
            self.settings.New('z_target',   ro=False, **pos_kwargs)

        self.settings.New('velocity', dtype=float, initial=2.0,
                          unit='mm/s', spinbox_decimals=2,
                          spinbox_step=0.5, vmin=0.01, vmax=10.0)
        self.settings.New('serial_number', dtype=int, initial=0,
                          description='Set to 0 to grab first available device')
        self.settings.New('axis_x', dtype=int, initial=2, vmin=1, vmax=6,
                          description='MCL axis number for X (M1=1 … M6=6)')
        self.settings.New('axis_y', dtype=int, initial=1, vmin=1, vmax=6,
                          description='MCL axis number for Y (M1=1 … M6=6)')
        self.settings.New('encoder_x', dtype=int, initial=1, vmin=0, vmax=3,
                          description='Encoder index for X position (0-based)')
        self.settings.New('encoder_y', dtype=int, initial=0, vmin=0, vmax=3,
                          description='Encoder index for Y position (0-based)')
        self.settings.New('invert_x', dtype=bool, initial=False)
        self.settings.New('invert_y', dtype=bool, initial=True)

        self.settings.New('at_limit', dtype=bool, ro=True, initial=False)
        self.settings.New('x_min', dtype=float, ro=True, initial=0.0, unit='mm', spinbox_decimals=4)
        self.settings.New('x_max', dtype=float, ro=True, initial=0.0, unit='mm', spinbox_decimals=4)
        self.settings.New('y_min', dtype=float, ro=True, initial=0.0, unit='mm', spinbox_decimals=4)
        self.settings.New('y_max', dtype=float, ro=True, initial=0.0, unit='mm', spinbox_decimals=4)

        self.add_operation('Stop', self.stop)
        self.add_operation('Reset Encoders', self.reset_encoders)

        self._update_timer = QtCore.QTimer()
        self._update_timer.timeout.connect(self._on_update_timer)
        self._update_timer.start(200)

    def connect(self):
        S = self.settings
        serial = S['serial_number'] or None
        self.stage = MCLMicrostage(serial_num=serial, debug=S['debug_mode'],
                                   axis_x=S['axis_x'], axis_y=S['axis_y'],
                                   encoder_x=S['encoder_x'], encoder_y=S['encoder_y'],
                                   invert_x=S['invert_x'], invert_y=S['invert_y'])

        # Update velocity limits from device and set a safe default
        S.velocity.change_min_max(self.stage.min_velocity, self.stage.max_velocity)
        S['velocity'] = self.stage._default_velocity

        if self.enable_x:
            S.x_position.connect_to_hardware(read_func=self.stage.read_pos_x)
            S.x_position.read_from_hardware()
            S['x_target'] = S['x_position']
            S.x_target.connect_to_hardware(
                write_func=lambda v: self.stage.move_x(v, S['velocity']))

        if self.enable_y:
            S.y_position.connect_to_hardware(read_func=self.stage.read_pos_y)
            S.y_position.read_from_hardware()
            S['y_target'] = S['y_position']
            S.y_target.connect_to_hardware(
                write_func=lambda v: self.stage.move_y(v, S['velocity']))

        if self.enable_z:
            S.z_position.connect_to_hardware(read_func=self.stage.read_pos_z)
            S.z_position.read_from_hardware()
            S['z_target'] = S['z_position']
            S.z_target.connect_to_hardware(
                write_func=lambda v: self.stage.move_z(v, S['velocity']))

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'stage'):
            self.stage.close()
            del self.stage

    def _on_update_timer(self):
        if not self.settings['connected']:
            return
        self.settings['at_limit'] = self.stage.is_at_any_limit()
        if self.enable_x:
            self.settings.x_position.read_from_hardware()
        if self.enable_y:
            self.settings.y_position.read_from_hardware()
        if self.enable_z:
            self.settings.z_position.read_from_hardware()

    def stop(self):
        self.stage.stop()

    def reset_encoders(self):
        self.stage.reset_encoders()
        if self.enable_x:
            self.settings['x_target'] = 0.0
        if self.enable_y:
            self.settings['y_target'] = 0.0
        if self.enable_z:
            self.settings['z_target'] = 0.0

    # ------------------------------------------------------------------
    # Convenience methods for use from measurements / MCP
    # ------------------------------------------------------------------

    def move_x(self, x):
        self.settings['x_target'] = x

    def move_y(self, y):
        self.settings['y_target'] = y

    def move_rel_x(self, delta):
        self.stage.move_rel_x(delta, self.settings['velocity'])

    def move_rel_y(self, delta):
        self.stage.move_rel_y(delta, self.settings['velocity'])

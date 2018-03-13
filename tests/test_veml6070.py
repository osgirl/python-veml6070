
# import unittest
import sys
import time

import mock

import snapshottest

# Note: prepare globally mocked modules first and then load our module
MOCKED_SMBUS_MODULE = mock.Mock()
sys.modules['smbus'] = MOCKED_SMBUS_MODULE
time.sleep = lambda s: None
import veml6070

# inspired by https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/I2C.py
class MockSMBus(object):
    def __init__(self, initial_read=None):
        self._writelog = {}
        self._readlog = {}
        self.initial_read = initial_read or {}

    def read_byte(self, addr):
        val = self.initial_read.get(addr).pop(0)
        self._readlog.setdefault(addr, []).append(val)
        return val

    def write_byte(self, addr, val):
        self._writelog.setdefault(addr, []).append(val)

    def _get_log(self):
        return {
            'readlog': [(str(key), value) for (key, value) in self._readlog.items()],
            'writelog': [(str(key), value) for (key, value) in self._writelog.items()]
        }

# def create_veml6070(**kwargs):
#     mockbus = MockSMBus()
#     smbus = Mock()
#     smbus.SMBus.return_value = mockbus
#     with patch.dict('sys.modules', {'smbus': smbus}):
#         import veml6070
#         # Note: our module constants only available in this scope
#         return (veml6070.Veml6070(**kwargs), mockbus)

def setup_mockbus(**kwargs):
    mockbus = MockSMBus(**kwargs)
    MOCKED_SMBUS_MODULE.SMBus.return_value = mockbus
    return mockbus

class TestVeml6070(snapshottest.TestCase):

    def test_setup(self):
        mockbus = setup_mockbus()
        veml = veml6070.Veml6070()
        self.assertIsNotNone(veml)
        self.assertMatchSnapshot(mockbus._get_log())

    def test_integration_time(self):
        mockbus = setup_mockbus()
        veml = veml6070.Veml6070(integration_time=veml6070.INTEGRATIONTIME_1_2T)
        self.assertEqual(veml.get_integration_time(), veml6070.INTEGRATIONTIME_1_2T)
        veml.set_integration_time(veml6070.INTEGRATIONTIME_4T)
        self.assertEqual(veml.get_integration_time(), veml6070.INTEGRATIONTIME_4T)
        self.assertMatchSnapshot(mockbus._get_log())

    def test_enable(self):
        mockbus = setup_mockbus()
        veml = veml6070.Veml6070()
        veml.enable()
        self.assertMatchSnapshot(mockbus._get_log())

    def test_disable(self):
        mockbus = setup_mockbus()
        veml = veml6070.Veml6070()
        veml.disable()
        self.assertMatchSnapshot(mockbus._get_log())

    def test_uva_light_intensity_raw(self):
        mockbus = setup_mockbus(initial_read={
            0x38+1: [0x12],
            0x38+0: [0x34]
        })
        veml = veml6070.Veml6070()
        self.assertEqual(veml.get_uva_light_intensity_raw(), 0x1234)
        self.assertMatchSnapshot(mockbus._get_log())

    def test_uva_light_intensity(self):
        mockbus = setup_mockbus(initial_read={
            0x38+1: [0x01, 0x01],
            0x38+0: [0x06, 0x06]
        })
        veml = veml6070.Veml6070()
        self.assertEqual(veml.get_uva_light_intensity(), 0x0106 * 0.05625 / 1)
        veml.set_integration_time(veml6070.INTEGRATIONTIME_4T)
        self.assertEqual(veml.get_uva_light_intensity(), 0x0106 * 0.05625 / 4)
        self.assertMatchSnapshot(mockbus._get_log())
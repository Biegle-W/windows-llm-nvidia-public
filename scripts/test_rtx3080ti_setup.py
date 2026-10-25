"""Guard tests; do not execute firmware or use physical GPU memory."""
import copy
import unittest
from rtx3080ti_setup import inventory, require_3080_profile, require_installed_board

VALID='NVIDIA GeForce RTX 3080 Ti, 00000000:01:00.0, 0x220810DE, 0x12341458, 94.02.example, 12288, 350, 610.88, GPU-test'


class SetupGuardTests(unittest.TestCase):
    def test_inventory(self):
        self.assertEqual(inventory(VALID)['total_mib'],12288)

    def test_other_models(self):
        for text in (VALID.replace('RTX 3080 Ti','RTX 3060'),VALID.replace('220810DE','250310DE')):
            with self.assertRaises(RuntimeError):inventory(text)

    def test_multiple_cards(self):
        with self.assertRaises(RuntimeError):inventory(VALID+'\n'+VALID)

    def test_short_memory(self):
        with self.assertRaises(RuntimeError):inventory(VALID.replace('12288','8192'))

    def test_invalid_identity(self):
        for text in ('',VALID.replace('00000000:01:00.0','invalid'),VALID.replace('GPU-test','')):
            with self.assertRaises(RuntimeError):inventory(text)

    def test_requires_complete_physical_capture(self):
        profile={'target':{'vendorId':'10de','deviceId':'2208','architecture':'GA102'},'validation':{'probeComplete':True,'unlockApproved':False,'firmwareCompatible':False,'hardwareTested':False}}
        require_3080_profile(profile)
        for field,value in (('deviceId','2503'),('architecture','GA106')):
            wrong=copy.deepcopy(profile);wrong['target'][field]=value
            with self.assertRaises(RuntimeError):require_3080_profile(wrong)
        for field in profile['validation']:
            wrong=copy.deepcopy(profile);wrong['validation'][field]=not wrong['validation'][field]
            with self.assertRaises(RuntimeError):require_3080_profile(wrong)

    def test_installed_board_binding(self):
        profile={'target':{'vendorId':'10de','deviceId':'2208','architecture':'GA102',
            'subsystemVendorId':'10de','subsystemDeviceId':'1535','pciAddress':'0000:01:00.0'},
            'validation':{'probeComplete':True,'unlockApproved':False,'firmwareCompatible':False,'hardwareTested':False}}
        require_installed_board(profile)
        for field,value in (('subsystemVendorId','1458'),('subsystemDeviceId','1234'),('pciAddress','0000:02:00.0')):
            wrong=copy.deepcopy(profile);wrong['target'][field]=value
            with self.assertRaises(RuntimeError):require_installed_board(wrong)


if __name__=='__main__':unittest.main()

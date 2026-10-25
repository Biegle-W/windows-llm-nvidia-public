"""3080 10GB identity/profile guards; no GPU execution."""
import copy
import unittest
from rtx3080_setup import inventory,require_profile

VALID='NVIDIA GeForce RTX 3080, 00000000:01:00.0, 0x220610DE, 0x12341458, 94.02.fixture, 10240, 320, 610.88, GPU-fixture'


class SetupTests(unittest.TestCase):
    def test_valid_identity(self):
        card=inventory(VALID);self.assertEqual(card['bdf'],'0000:01:00.0');self.assertEqual(card['total_mib'],10240)

    def test_wrong_model(self):
        for name in ('NVIDIA GeForce RTX 3060','NVIDIA GeForce RTX 3080 Ti'):
            with self.assertRaises(RuntimeError):inventory(VALID.replace('NVIDIA GeForce RTX 3080',name))

    def test_wrong_pci(self):
        for pci in ('0x220810DE','0x221610DE','0x250310DE'):
            with self.assertRaises(RuntimeError):inventory(VALID.replace('0x220610DE',pci))

    def test_wrong_capacity(self):
        for capacity in ('12288','20480'):
            with self.assertRaises(RuntimeError):inventory(VALID.replace('10240',capacity))

    def test_multiple_cards(self):
        with self.assertRaises(RuntimeError):inventory(VALID+'\n'+VALID)

    def test_incomplete_identity(self):
        for text in (VALID.replace('GPU-fixture',''),VALID.replace('00000000:01:00.0','invalid'),VALID.replace('0x12341458','invalid')):
            with self.assertRaises(RuntimeError):inventory(text)

    def profile(self):
        return {'target':dict(vendorId='10de',deviceId='2206',architecture='GA102',
            subsystemVendorId='1458',subsystemDeviceId='1234',pciAddress='0000:01:00.0'),
            'validation':dict(probeComplete=True,unlockApproved=False,firmwareCompatible=False,hardwareTested=False)}

    def test_profile_matches_windows(self):
        require_profile(self.profile(),inventory(VALID))

    def test_profile_wrong_board(self):
        for field,value in [('deviceId','2208'),('subsystemDeviceId','5678'),('pciAddress','0000:02:00.0')]:
            p=self.profile();p['target'][field]=value
            with self.assertRaises(RuntimeError):require_profile(p,inventory(VALID))

    def test_validation_flags(self):
        for field in self.profile()['validation']:
            p=self.profile();p['validation'][field]=not p['validation'][field]
            with self.assertRaises(RuntimeError):require_profile(p,inventory(VALID))


if __name__=='__main__':unittest.main()

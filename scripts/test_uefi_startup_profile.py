"""CPU-only provenance tests for the fixed automatic startup profile."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import prepare_uefi_3060_automatic as builder


class StartupEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='startup-evidence-test-', dir=builder.ROOT/'data/uefi-probe/captures')
        self.folder = Path(self.temp.name)
        source = json.loads((builder.ROOT/'data/uefi-probe/internal-startup/automatic-first-boot-capture.private.json').read_text(encoding='utf-8'))
        self.capture = copy.deepcopy(source)
        for row in source['Logs']:
            (self.folder/row['Name']).write_bytes((Path(source['CaptureDirectory'])/row['Name']).read_bytes())
        self.capture['CaptureDirectory'] = str(self.folder)
        self.path = self.folder/'capture.json'
        self.header = (builder.ROOT/'data/uefi-probe/windows3060-unlock-20261025-v2/private-board-profile.h').read_text(encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def call(self):
        self.path.write_text(json.dumps(self.capture), encoding='utf-8')
        return builder.observed_zero_profile(self.path, self.header)

    def alter_log(self, name, old, new):
        p=self.folder/name
        text=p.read_text(encoding='utf-8')
        self.assertIn(old,text)
        p.write_text(text.replace(old,new),encoding='utf-8')
        for row in self.capture['Logs']:
            if row['Name']==name:
                row.update(Sha256=builder.sha(p),Bytes=p.stat().st_size)

    def test_only_two_constants_change(self):
        header,_=self.call()
        changed=[(a,b) for a,b in zip(self.header.splitlines(),header.splitlines()) if a!=b]
        self.assertEqual(len(changed),2)
        self.assertTrue(all('GU_INITIAL_SS' in a for a,b in changed))

    def test_failed_capture(self):
        self.capture['Success']=False
        with self.assertRaises(RuntimeError): self.call()

    def test_wrong_efi(self):
        self.capture['EfiSha256']='0'*64
        with self.assertRaises(RuntimeError): self.call()

    def test_wrong_run(self):
        self.capture['LogRun']='RUN0001'
        with self.assertRaises(RuntimeError): self.call()

    def test_log_tampering(self):
        with (self.folder/'UNLOCK.TXT').open('a',encoding='utf-8') as f: f.write('tampered')
        with self.assertRaises(RuntimeError): self.call()

    def test_wrong_board_even_with_updated_hash(self):
        self.alter_log('UNLOCK.TXT','pci=0x250310de','pci=0x220810de')
        with self.assertRaises(RuntimeError): self.call()

    def test_nonzero_state_even_with_updated_hash(self):
        self.alter_log('UNLOCK.TXT','WPR2_HI=0 SS0=0 SS1=0','WPR2_HI=0 SS0=0x88888888 SS1=0x8')
        with self.assertRaises(RuntimeError): self.call()

    def test_touched_capture_even_with_updated_hash(self):
        self.alter_log('GOP.TXT','touched=0','touched=1')
        with self.assertRaises(RuntimeError): self.call()

    def test_wrong_original_header(self):
        self.header=self.header.replace('GU_INITIAL_SS1 0x00000005U','GU_INITIAL_SS1 0x00000007U')
        with self.assertRaises(RuntimeError): self.call()

    def test_path_outside_private_capture(self):
        self.capture['CaptureDirectory']=str(builder.ROOT/'reports')
        with self.assertRaises(RuntimeError): self.call()

    def test_two_observed_complete_pairs(self):
        zero,_=self.call()
        path=builder.ROOT/'data/uefi-probe/internal-startup/paired-startup-repeat-evidence.private.json'
        header,proof=builder.observed_paired_profile(zero,path)
        self.assertIn('GuCapturedStartupSelectorsMatch',header)
        self.assertEqual(proof['allowed_initial_pairs'],[['00000000','00000000'],['70520074','00000005']])

    def test_paired_capture_wrong_run(self):
        zero,_=self.call()
        real=builder.ROOT/'data/uefi-probe/internal-startup/paired-startup-repeat-evidence.private.json'
        repeat=json.loads(real.read_text(encoding='utf-8'));repeat['LogRun']='RUN0004'
        path=self.folder/'bad-repeat.json';path.write_text(json.dumps(repeat),encoding='utf-8')
        with self.assertRaises(RuntimeError): builder.observed_paired_profile(zero,path)

    def test_paired_capture_wrong_hash(self):
        zero,_=self.call()
        real=builder.ROOT/'data/uefi-probe/internal-startup/paired-startup-repeat-evidence.private.json'
        repeat=json.loads(real.read_text(encoding='utf-8'));repeat['Logs'][0]['Sha256']='0'*64
        path=self.folder/'bad-repeat.json';path.write_text(json.dumps(repeat),encoding='utf-8')
        with self.assertRaises(RuntimeError): builder.observed_paired_profile(zero,path)


if __name__=='__main__':
    unittest.main()

"""Synthetic ownership-policy tests; no physical GPU, raw capture or firmware execution."""
from pathlib import Path
import tempfile
import unittest

from prepare_uefi_3080ti_manual import validate_tree
from prepare_uefi_3060_single_child import read_tree, board_pair


def fixture():
    lines=['STAGE secure-boot query=0 bytes=1 enabled=0','target=0x100 BDF=0:1:0.0',
        'config_before[00]=220810de','config_before[2c]=153510de','TREE_BEGIN root=0x100',
        'TREE_NODE handle=0x400 depth=3 console_out=1 console_in=1 stderr=1']
    edges=[('100','09576e91',8,'501','200'),('100','4cf5b200',16,'501','100'),
        ('200','9042a9de',8,'502','300'),('200','9042a9de',16,'502','200'),
        ('200','1c0c34f6',16,'505','200'),('300','387477c2',8,'504','400'),
        ('300','387477c2',16,'504','300'),('300','9042a9de',16,'503','300'),
        ('400','8d59d32b',16,'505','400'),('400','31878c87',16,'505','400')]
    for h,protocol,attr,agent,child in edges:
        lines.append(f'TREE_OPEN handle=0x{h} protocol={protocol} attr={hex(attr)} count=1 agent=0x{agent} controller=0x{child}')
    for i in range(1,6):
        agent=f'0x50{i}';base=0x100000*i
        lines.append(f'TREE_BINDING agent={agent} binding={agent} image={agent} version=0x1 start={hex(base+0x100)} stop={hex(base+0x200)}')
        lines.append(f'TREE_IMAGE_INFO agent={agent} base={hex(base)} bytes=4096 code_type={5 if i==5 else 3}')
    lines+=['TREE_END status=0 complete=1 visited=4 queued=4 drivers=5 opens=38 detach_attempted=0',
        'TREE_RESULT status=0 touched=0']
    return '\n'.join(lines)+'\n'


class OwnershipPolicyTests(unittest.TestCase):
    def check(self,text,valid=False):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'GOP.TXT';path.write_text(text,encoding='ascii')
            if valid:return validate_tree(path)
            with self.assertRaises(RuntimeError):validate_tree(path)

    def test_valid_tree(self):
        self.assertEqual(len(self.check(fixture(),True)),5)

    def test_wrong_board(self):
        for old,new in [('220810de','250310de'),('153510de','123410de'),('BDF=0:1:0.0','BDF=0:2:0.0')]:
            self.check(fixture().replace(old,new))

    def test_incomplete_or_touched(self):
        for old,new in [('complete=1','complete=0'),('touched=0','touched=1'),('detach_attempted=0','detach_attempted=1')]:
            self.check(fixture().replace(old,new))

    def test_extra_owner(self):
        self.check(fixture().replace('TREE_RESULT','TREE_OPEN handle=0x100 protocol=12345678 attr=0x8 count=1 agent=0x501 controller=0x200\nTREE_RESULT'))

    def test_wrong_count(self):
        self.check(fixture().replace('count=1 agent=0x501','count=2 agent=0x501',1))

    def test_runtime_input_driver_type(self):
        self.check(fixture().replace('code_type=5','code_type=3'))

    def test_shared_input_output_changed(self):
        self.check(fixture().replace('console_out=1 console_in=1','console_out=1 console_in=0'))

    def test_3060_default_remains_scoped(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'GOP.TXT';path.write_text(fixture(),encoding='ascii')
            with self.assertRaises(RuntimeError):read_tree(path)

    def test_unreviewed_pair(self):
        with self.assertRaises(RuntimeError):board_pair('220810de','407b1458')


if __name__=='__main__':unittest.main()

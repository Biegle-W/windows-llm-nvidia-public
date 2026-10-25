"""GPU-swap selection regressions; no GPU process is started."""
import unittest
from hardware_guard import choose_gpu, validate_devices


class GpuSwapGuardTests(unittest.TestCase):
    def test_each_supported_card(self):
        for model in ('3060','3080 Ti'):
            name='NVIDIA GeForce RTX '+model
            self.assertEqual(choose_gpu(f'{name}, GPU-test, 12288, 11000')['name'],name)
            self.assertEqual(validate_devices(f'  CUDA0: {name} (12288 MiB, 11000 MiB free)',expected_name=name)[0]['name'],name)

    def test_multiple_cards_rejected(self):
        with self.assertRaises(RuntimeError): choose_gpu('NVIDIA GeForce RTX 3060, GPU-a, 12288, 11000\nNVIDIA GeForce RTX 3080 Ti, GPU-b, 12288, 11000')

    def test_unknown_card_rejected(self):
        with self.assertRaises(RuntimeError): choose_gpu('NVIDIA GeForce RTX 4070, GPU-a, 12288, 11000')

    def test_8gb_3060_rejected(self):
        with self.assertRaises(RuntimeError): choose_gpu('NVIDIA GeForce RTX 3060, GPU-a, 8192, 8000')

    def test_invalid_inventory_rejected(self):
        for text in ('','broken','NVIDIA GeForce RTX 3060, , 12288, 11000','NVIDIA GeForce RTX 3060, GPU-a, N/A, 11000','NVIDIA GeForce RTX 3060, GPU-a, 12288, 13000'):
            with self.subTest(text=text), self.assertRaises(RuntimeError): choose_gpu(text)

    def test_wrong_runtime_card_rejected(self):
        with self.assertRaises(RuntimeError): validate_devices('CUDA0: NVIDIA GeForce RTX 3080 Ti (12288 MiB, 11000 MiB free)',expected_name='NVIDIA GeForce RTX 3060')

    def test_runtime_requires_single_cuda0(self):
        for text in ('CUDA1: NVIDIA GeForce RTX 3060 (12288 MiB, 11000 MiB free)','CUDA0: NVIDIA GeForce RTX 3060 (12288 MiB, 11000 MiB free)\nCUDA1: NVIDIA GeForce RTX 3080 Ti (12288 MiB, 11000 MiB free)'):
            with self.assertRaises(RuntimeError): validate_devices(text)

    def test_vram_guard_retained(self):
        with self.assertRaises(RuntimeError): validate_devices('CUDA0: NVIDIA GeForce RTX 3080 Ti (12288 MiB, 1000 MiB free)')


if __name__=='__main__': unittest.main()

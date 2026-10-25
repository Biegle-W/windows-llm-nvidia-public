"""Host-only safety/rollback tests; no real driver, boot image or GPU access."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("unlock", Path(__file__).with_name("native_linux_gpu_unlock.py"))
unlock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unlock)


class Guards(unittest.TestCase):
    @staticmethod
    def shell():
        git_bash = Path("C:/Program Files/Git/bin/bash.exe")
        return str(git_bash) if git_bash.is_file() else shutil.which("bash")

    def test_generated_shell_syntax(self):
        shell = self.shell()
        if not shell:
            self.skipTest("bash not installed")
        for content in unlock.boot_files("0000:01:00.0").values():
            subprocess.run([shell, "-n"], input=content, text=True, check=True)

    def test_grub_retains_existing_arguments(self):
        shell = self.shell()
        if not shell:
            self.skipTest("bash not installed")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owned.cfg"
            path.write_text(unlock.boot_files("0000:01:00.0")[unlock.GRUB])
            result = subprocess.run([shell, "-c", 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash test=existing"; '
                                     '. "$1"; printf "%s" "$GRUB_CMDLINE_LINUX_DEFAULT"', "check",
                                     str(path).replace("\\", "/")], check=True, capture_output=True, text=True)
            self.assertEqual(result.stdout, "quiet splash test=existing gpu_unlock.targets=0000:01:00.0")

    def test_windows_and_wsl_refused_before_mutation(self):
        for system, release in (("Windows", "11"), ("Linux", "6.18-microsoft-standard-WSL2")):
            with self.subTest(system=system), patch.object(unlock.platform, "system", return_value=system), \
                 patch.object(unlock.platform, "release", return_value=release), patch.object(unlock, "run") as run:
                with self.assertRaises(RuntimeError):
                    unlock.install()
                run.assert_not_called()

    def test_retail_targets_and_rejected_engineering_model(self):
        cards = [{"bdf": "0000:01:00.0", "device": "2503"},
                 {"bdf": "0000:02:00.0", "device": "2208"},
                 {"bdf": "0000:03:00.0", "device": "2205"}]
        self.assertEqual(unlock.targets("0000:01:00.0,0000:02:00.0", cards),
                         "0000:01:00.0,0000:02:00.0")
        for value in ("all", "0000:03:00.0", "0000:04:00.0", "0000:01:00.0,0000:01:00.0",
                      "0000:01:00.0;reboot"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                unlock.targets(value, cards)

    def test_audio_function_is_not_a_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bdf, pci_class in (("gpu0", "0x030000"), ("audio0", "0x040300")):
                folder = Path(tmp) / bdf
                folder.mkdir()
                for name, value in (("vendor", "0x10de"), ("class", pci_class), ("device", "0x2503")):
                    (folder / name).write_text(value)
            self.assertEqual([card["bdf"] for card in unlock.devices(Path(tmp))], ["gpu0"])

    def test_secure_boot_enabled_or_unknown_blocks_install(self):
        for state in ("enabled", "unknown"):
            with patch.object(unlock, "prerequisites"), patch.object(unlock, "secure_boot", return_value=state), \
                 patch.object(unlock, "prepare_source") as source:
                with self.assertRaises(RuntimeError):
                    unlock.install()
                source.assert_not_called()

    def test_generation_failure_restores_dropin_and_rebuilds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owned.cfg"
            original = unlock.MARKER + "original options\n"
            path.write_text(original)
            failure = subprocess.CalledProcessError(1, "update-grub")
            with patch.object(unlock, "run", side_effect=["", failure, "", ""]) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    unlock.transactional_update({path: unlock.MARKER + "new options\n"})
                self.assertEqual(path.read_text(), original)
                self.assertEqual(run.call_count, 4)

    def test_unowned_configuration_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "other.cfg"
            path.write_text("user configuration\n")
            with patch.object(unlock, "run") as run:
                with self.assertRaises(RuntimeError):
                    unlock.transactional_update({path: None})
                run.assert_not_called()
            self.assertEqual(path.read_text(), "user configuration\n")

    def test_missing_module_in_image_rolls_back_before_grub(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owned.cfg"
            with patch.object(unlock, "run", return_value="") as run:
                with self.assertRaises(RuntimeError):
                    unlock.transactional_update({path: unlock.MARKER}, verify_image=True)
                self.assertFalse(path.exists())
                self.assertEqual(run.call_args_list[2].args, ("update-initramfs", "-u", "-k", "all"))

    def test_disable_needs_no_gpu_or_secure_boot_checks(self):
        with patch.object(unlock, "native_only"), patch.object(unlock.os, "geteuid", return_value=0, create=True), \
             patch.object(unlock, "transactional_update") as update, patch.object(unlock, "mutation_gate") as gate:
            unlock.disable()
            gate.assert_not_called()
            self.assertEqual(set(update.call_args.args[0].values()), {None})


if __name__ == "__main__":
    unittest.main()

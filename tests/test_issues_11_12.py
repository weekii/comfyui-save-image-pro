import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


class FilenameAndCounterIssueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[1]
        cls.pkg_name = "comfyui_save_image_pro_testpkg_issues"
        pkg = types.ModuleType(cls.pkg_name)
        pkg.__path__ = [str(cls.repo)]
        sys.modules[cls.pkg_name] = pkg
        for name in ["core.config", "core.filename_generator", "core.counter_manager"]:
            spec = importlib.util.spec_from_file_location(
                f"{cls.pkg_name}.{name}", cls.repo / (name.replace(".", "/") + ".py")
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
        cls.SaveConfig = sys.modules[f"{cls.pkg_name}.core.config"].SaveConfig
        cls.FileNameGenerator = sys.modules[f"{cls.pkg_name}.core.filename_generator"].FileNameGenerator
        cls.CounterManager = sys.modules[f"{cls.pkg_name}.core.counter_manager"].CounterManager

    def test_issue_12_slash_mixed_folder_keys_create_nested_model_date_path(self):
        prompt = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model_x.safetensors"},
            }
        }
        config = self.SaveConfig(
            foldername_prefix="",
            foldername_keys="/img2img/ckpt_name/%F",
            delimiter="-",
            filename_prefix="test",
            filename_keys="",
        )
        folder = self.FileNameGenerator(config).generate_foldername(prompt)
        self.assertRegex(folder, r"^img2img[\\/]model_x[\\/]\d{4}-\d{2}-\d{2}$")

    def test_issue_11_counter_uses_configured_underscore_delimiter_last(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "foo_0001.webp").write_text("x")
            counter = self.CounterManager().get_next_counter(
                d, "foo", 4, "last", ".webp", True, delimiter="_"
            )
            self.assertEqual(counter, 2)

    def test_issue_11_counter_uses_configured_underscore_delimiter_first(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "0001_foo.webp").write_text("x")
            counter = self.CounterManager().get_next_counter(
                d, "foo", 4, "first", ".webp", True, delimiter="_"
            )
            self.assertEqual(counter, 2)


if __name__ == "__main__":
    unittest.main()

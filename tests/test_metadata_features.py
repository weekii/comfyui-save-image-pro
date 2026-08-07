import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


class FakeTensor:
    def __init__(self, array):
        self._array = array
        self.shape = array.shape

    def cpu(self):
        return self

    def numpy(self):
        return self._array

    def __getitem__(self, key):
        return FakeTensor(self._array[key])


class SaveImageMetadataFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[1]
        cls.pkg_name = "comfyui_save_image_pro_testpkg_features"
        pkg = types.ModuleType(cls.pkg_name)
        pkg.__path__ = [str(cls.repo)]
        sys.modules[cls.pkg_name] = pkg

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder_paths = types.ModuleType("folder_paths")
        folder_paths.get_output_directory = lambda: self.tmp.name
        sys.modules["folder_paths"] = folder_paths

        for name in ["save_image_advanced", "save_image_simple"]:
            spec = importlib.util.spec_from_file_location(
                f"{self.pkg_name}.{name}", self.repo / f"{name}.py"
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)

        self.Advanced = sys.modules[f"{self.pkg_name}.save_image_advanced"].SaveImageAdvanced
        self.Simple = sys.modules[f"{self.pkg_name}.save_image_simple"].SaveImageSimple
        self.images = [FakeTensor(np.zeros((8, 16, 3), dtype=np.float32))]
        self.prompt = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model_x.safetensors"}},
            "2": {"class_type": "KSampler", "inputs": {"seed": 123, "steps": 30, "cfg": 7.5, "sampler_name": "euler", "scheduler": "normal"}},
        }
        self.extra = {"workflow": {"nodes": [{"id": 1, "type": "CheckpointLoaderSimple"}]}}

    def tearDown(self):
        self.tmp.cleanup()

    def saved_path(self, result):
        item = result["ui"]["images"][0]
        return Path(self.tmp.name) / item["subfolder"] / item["filename"]

    def image_text(self, path):
        with Image.open(path) as im:
            return dict(im.text)

    def test_metadata_mode_a1111_writes_parameters_without_workflow(self):
        result = self.Advanced().save_images(
            self.images,
            filename_prefix="a1111_only",
            filename_keys="",
            foldername_keys="",
            output_format=".png",
            save_metadata=True,
            metadata_mode="a1111",
            prompt=self.prompt,
            extra_pnginfo=self.extra,
            positive_text="a castle",
            negative_text="blur",
        )
        text = self.image_text(self.saved_path(result))

        self.assertNotIn("prompt", text)
        self.assertNotIn("workflow", text)
        self.assertIn("parameters", text)
        self.assertIn("a castle", text["parameters"])
        self.assertIn("Negative prompt: blur", text["parameters"])
        self.assertIn("Steps: 30", text["parameters"])
        self.assertIn("CFG scale: 7.5", text["parameters"])
        self.assertIn("Seed: 123", text["parameters"])
        self.assertIn("Size: 16x8", text["parameters"])
        self.assertIn("Model: model_x", text["parameters"])

    def test_metadata_mode_both_and_sidecars_write_expected_files(self):
        result = self.Advanced().save_images(
            self.images,
            filename_prefix="both_sidecar",
            filename_keys="",
            foldername_keys="",
            output_format=".png",
            save_metadata=True,
            metadata_mode="comfy+a1111",
            sidecar_mode="both",
            prompt=self.prompt,
            extra_pnginfo=self.extra,
            positive_text="sunset",
            negative_text="noise",
        )
        image_path = self.saved_path(result)
        text = self.image_text(image_path)

        self.assertIn("prompt", text)
        self.assertIn("workflow", text)
        self.assertIn("parameters", text)

        txt_path = image_path.with_suffix(".txt")
        json_path = image_path.with_suffix(".json")
        self.assertTrue(txt_path.exists())
        self.assertTrue(json_path.exists())
        self.assertIn("sunset", txt_path.read_text(encoding="utf-8"))
        sidecar = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(sidecar["prompt"], self.prompt)
        self.assertEqual(sidecar["workflow"], self.extra["workflow"])
        self.assertIn("parameters", sidecar)

    def test_simple_metadata_mode_off_disables_existing_boolean_path(self):
        result = self.Simple().save_images(
            self.images,
            filename_prefix="simple_off",
            output_format=".png",
            save_image_metadata=True,
            metadata_mode="off",
            prompt=self.prompt,
            extra_pnginfo=self.extra,
        )
        text = self.image_text(self.saved_path(result))
        self.assertNotIn("prompt", text)
        self.assertNotIn("workflow", text)
        self.assertNotIn("parameters", text)

    def test_jpeg_a1111_mode_writes_parameters_to_exif_description(self):
        result = self.Advanced().save_images(
            self.images,
            filename_prefix="jpeg_a1111",
            filename_keys="",
            foldername_keys="",
            output_format=".jpg",
            save_metadata=True,
            metadata_mode="a1111",
            prompt=self.prompt,
            extra_pnginfo=self.extra,
            positive_text="portrait",
            negative_text="bad hands",
        )
        image_path = self.saved_path(result)
        with Image.open(image_path) as im:
            exif = im.getexif()
        description = exif.get(0x010e, "")
        user_comment = exif.get(0x9286, b"")
        if isinstance(user_comment, bytes):
            user_comment = user_comment.decode("utf-8", errors="ignore")
        self.assertIn("portrait", description)
        self.assertIn("Steps: 30", description)
        self.assertIn("portrait", user_comment)


if __name__ == "__main__":
    unittest.main()

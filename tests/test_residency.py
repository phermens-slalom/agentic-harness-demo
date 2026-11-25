import unittest

from harness.residency import ResidencyError, assert_allowed, assert_model_backend


class ResidencyTests(unittest.TestCase):
    def test_allowed(self):
        self.assertEqual(assert_allowed("australia-southeast2"), "australia-southeast2")

    def test_global_and_unset_rejected(self):
        for loc in ("global", "us-central1", None, ""):
            with self.assertRaises(ResidencyError):
                assert_allowed(loc)


VERTEX = {"GOOGLE_GENAI_USE_VERTEXAI": "TRUE", "GOOGLE_CLOUD_LOCATION": "australia-southeast2"}


class ModelBackendTests(unittest.TestCase):
    def test_vertex_in_an_allowed_location_passes_anywhere(self):
        self.assertEqual(assert_model_backend(VERTEX), "vertex")
        self.assertEqual(assert_model_backend({**VERTEX, "GOOGLE_GENAI_USE_VERTEXAI": "1"}), "vertex")

    def test_vertex_in_a_bad_or_missing_location_fails_even_locally(self):
        for loc in ("global", "us-central1", None):
            env = {**VERTEX, "HARNESS_ENV": "local"}
            if loc is None:
                del env["GOOGLE_CLOUD_LOCATION"]
            else:
                env["GOOGLE_CLOUD_LOCATION"] = loc
            with self.assertRaises(ResidencyError):
                assert_model_backend(env)

    def test_ai_studio_is_allowed_only_when_harness_env_is_local(self):
        self.assertEqual(assert_model_backend({"HARNESS_ENV": "local", "GOOGLE_API_KEY": "k"}), "ai-studio")
        self.assertEqual(assert_model_backend({"HARNESS_ENV": "LOCAL"}), "ai-studio")
        for env in (
            {},
            {"GOOGLE_API_KEY": "k"},
            {"HARNESS_ENV": "prod", "GOOGLE_API_KEY": "k"},
            {"HARNESS_ENV": ""},
        ):
            with self.assertRaisesRegex(ResidencyError, "HARNESS_ENV=local"):
                assert_model_backend(env)

    def test_an_api_key_next_to_vertex_is_rejected_outside_local(self):
        with self.assertRaisesRegex(ResidencyError, "GOOGLE_API_KEY"):
            assert_model_backend({**VERTEX, "GOOGLE_API_KEY": "k"})
        self.assertEqual(
            assert_model_backend({**VERTEX, "GOOGLE_API_KEY": "k", "HARNESS_ENV": "local"}), "vertex"
        )


if __name__ == "__main__":
    unittest.main()

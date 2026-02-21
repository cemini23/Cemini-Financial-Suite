"""Tests for vertex_util.py."""

import unittest
from unittest.mock import patch

from scripts.internal_commands import vertex_util


class VertexUtilTest(unittest.TestCase):

    @patch("vertexai.init")
    @patch("builtins.print")
    def test_create_vertex_prompt(self, mock_print, mock_vertexai_init):
        vertex_util.create_vertex_prompt(
            content="test content",
            system_instruction="test system instruction",
            model="gemini-pro",
            display_name="test_display_name",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_vertexai_init.assert_called_once_with(
            project="test_project_id", location="test_location_id"
        )
        mock_print.assert_called_once()
        self.assertIn("Simulating prompt creation:", mock_print.call_args[0][0])

    @patch("vertexai.init")
    @patch("builtins.print")
    def test_read_vertex_prompt(self, mock_print, mock_vertexai_init):
        prompt_id = "test_prompt_id"
        result = vertex_util.read_vertex_prompt(
            prompt_id=prompt_id,
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_vertexai_init.assert_called_once_with(
            project="test_project_id", location="test_location_id"
        )
        mock_print.assert_called_once()
        self.assertIn("Simulating reading prompt with ID:", mock_print.call_args[0][0])
        self.assertEqual(result["id"], prompt_id)
        self.assertIn(prompt_id, result["display_name"])
        self.assertIn(prompt_id, result["content"])
        self.assertIn(prompt_id, result["system_instruction"])
        self.assertEqual(result["model"], "gemini-pro")

    @patch("vertexai.init")
    @patch("builtins.print")
    def test_update_vertex_prompt(self, mock_print, mock_vertexai_init):
        vertex_util.update_vertex_prompt(
            prompt_id="test_prompt_id",
            content="new content",
            system_instruction="new system instruction",
            model="gemini-flash",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_vertexai_init.assert_called_once_with(
            project="test_project_id", location="test_location_id"
        )
        mock_print.assert_called_once()
        self.assertIn("Simulating prompt update for ID:", mock_print.call_args[0][0])

    @patch("vertexai.init")
    @patch("builtins.print")
    def test_delete_vertex_prompt(self, mock_print, mock_vertexai_init):
        vertex_util.delete_vertex_prompt(
            prompt_id="test_prompt_id",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_vertexai_init.assert_called_once_with(
            project="test_project_id", location="test_location_id"
        )
        mock_print.assert_called_once()
        self.assertIn("Simulating prompt deletion for ID:", mock_print.call_args[0][0])

    @patch("vertexai.init")
    @patch("builtins.print")
    def test_list_vertex_prompts(self, mock_print, mock_vertexai_init):
        result = vertex_util.list_vertex_prompts(
            display_name="test_display_name",
            page_size=2,
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_vertexai_init.assert_called_once_with(
            project="test_project_id", location="test_location_id"
        )
        mock_print.assert_called_once()
        self.assertIn("Simulating listing prompts:", mock_print.call_args[0][0])
        self.assertEqual(len(result), 2)
        self.assertIn("Simulated Prompt", result[0]["display_name"])
        self.assertIn("Simulated content", result[0]["content"])
        self.assertIn("Simulated system instruction", result[0]["system_instruction"])
        self.assertEqual(result[0]["model"], "gemini-pro")


if __name__ == "__main__":
    unittest.main()

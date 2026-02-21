"""Tests for vertex_prompts.py."""

import unittest
from unittest.mock import patch

from scripts.internal_commands import vertex_prompts


class VertexPromptsTest(unittest.TestCase):

    @patch("scripts.internal_commands.vertex_util.create_vertex_prompt")
    def test_create_prompt(self, mock_create_vertex_prompt):
        vertex_prompts.create_prompt(
            content="test content",
            system_instruction="test system instruction",
            model="gemini-pro",
            display_name="test_display_name",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_create_vertex_prompt.assert_called_once_with(
            content="test content",
            system_instruction="test system instruction",
            model="gemini-pro",
            display_name="test_display_name",
            project_id="test_project_id",
            location_id="test_location_id",
        )

    @patch("scripts.internal_commands.vertex_util.read_vertex_prompt")
    def test_read_prompt(self, mock_read_vertex_prompt):
        vertex_prompts.read_prompt(
            prompt_id="test_prompt_id",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_read_vertex_prompt.assert_called_once_with(
            prompt_id="test_prompt_id",
            project_id="test_project_id",
            location_id="test_location_id",
        )

    @patch("scripts.internal_commands.vertex_util.update_vertex_prompt")
    def test_update_prompt(self, mock_update_vertex_prompt):
        vertex_prompts.update_prompt(
            prompt_id="test_prompt_id",
            content="new content",
            system_instruction="new system instruction",
            model="gemini-flash",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_update_vertex_prompt.assert_called_once_with(
            prompt_id="test_prompt_id",
            content="new content",
            system_instruction="new system instruction",
            model="gemini-flash",
            project_id="test_project_id",
            location_id="test_location_id",
        )

    @patch("scripts.internal_commands.vertex_util.delete_vertex_prompt")
    def test_delete_prompt(self, mock_delete_vertex_prompt):
        vertex_prompts.delete_prompt(
            prompt_id="test_prompt_id",
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_delete_vertex_prompt.assert_called_once_with(
            prompt_id="test_prompt_id",
            project_id="test_project_id",
            location_id="test_location_id",
        )

    @patch("scripts.internal_commands.vertex_util.list_vertex_prompts")
    def test_list_prompts(self, mock_list_vertex_prompts):
        vertex_prompts.list_prompts(
            display_name="test_display_name",
            page_size=2,
            project_id="test_project_id",
            location_id="test_location_id",
        )
        mock_list_vertex_prompts.assert_called_once_with(
            display_name="test_display_name",
            page_size=2,
            project_id="test_project_id",
            location_id="test_location_id",
        )


if __name__ == "__main__":
    unittest.main()

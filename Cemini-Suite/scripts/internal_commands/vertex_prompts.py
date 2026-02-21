"""Vertex AI Prompts.

This module provides tools for interacting with Google Cloud Vertex AI
prompt management.
"""

from typing import Optional

from google.cloud import aiplatform

from scripts.internal_commands import vertex_util


def create_prompt(
    content: str,
    system_instruction: str,
    model: str,
    display_name: str,
    project_id: Optional[str] = None,
    location_id: Optional[str] = None,
) -> None:
    """Creates a prompt in Vertex AI.

    Args:
        content: The content of the prompt.
        system_instruction: The system instruction for the prompt.
        model: The model to use for the prompt.
        display_name: The display name of the prompt.
        project_id: The Google Cloud project ID.
        location_id: The Google Cloud location ID.
    """
    vertex_util.create_vertex_prompt(
        content=content,
        system_instruction=system_instruction,
        model=model,
        display_name=display_name,
        project_id=project_id,
        location_id=location_id,
    )


def read_prompt(
    prompt_id: str,
    project_id: Optional[str] = None,
    location_id: Optional[str] = None,
) -> dict:
    """Reads a prompt from Vertex AI.

    Args:
        prompt_id: The ID of the prompt to read.
        project_id: The Google Cloud project ID.
        location_id: The Google Cloud location ID.

    Returns:
        A dictionary containing the prompt's information.
    """
    return vertex_util.read_vertex_prompt(
        prompt_id=prompt_id, project_id=project_id, location_id=location_id
    )


def update_prompt(
    prompt_id: str,
    content: Optional[str] = None,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    project_id: Optional[str] = None,
    location_id: Optional[str] = None,
) -> None:
    """Updates a prompt in Vertex AI.

    Args:
        prompt_id: The ID of the prompt to update.
        content: The new content of the prompt.
        system_instruction: The new system instruction for the prompt.
        model: The new model to use for the prompt.
        project_id: The Google Cloud project ID.
        location_id: The Google Cloud location ID.
    """
    vertex_util.update_vertex_prompt(
        prompt_id=prompt_id,
        content=content,
        system_instruction=system_instruction,
        model=model,
        project_id=project_id,
        location_id=location_id,
    )


def delete_prompt(
    prompt_id: str,
    project_id: Optional[str] = None,
    location_id: Optional[str] = None,
) -> None:
    """Deletes a prompt from Vertex AI.

    Args:
        prompt_id: The ID of the prompt to delete.
        project_id: The Google Cloud project ID.
        location_id: The Google Cloud location ID.
    """
    vertex_util.delete_vertex_prompt(
        prompt_id=prompt_id, project_id=project_id, location_id=location_id
    )


def list_prompts(
    display_name: Optional[str] = None,
    page_size: int = 10,
    project_id: Optional[str] = None,
    location_id: Optional[str] = None,
) -> list[dict]:
    """Lists prompts in Vertex AI.

    Args:
        display_name: Optional, filter by display name.
        page_size: The maximum number of prompts to return.
        project_id: The Google Cloud project ID.
        location_id: The Google Cloud location ID.

    Returns:
        A list of dictionaries, each containing a prompt's information.
    """
    return vertex_util.list_vertex_prompts(
        display_name=display_name,
        page_size=page_size,
        project_id=project_id,
        location_id=location_id,
    )

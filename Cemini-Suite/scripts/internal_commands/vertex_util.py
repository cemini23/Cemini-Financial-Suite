"""Utility functions for interacting with Google Cloud Vertex AI."""

from typing import Optional

import vertexai
from google.cloud import aiplatform


def create_vertex_prompt(
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
    if project_id and location_id:
        vertexai.init(project=project_id, location=location_id)
    elif project_id:
        vertexai.init(project=project_id)

    # TODO(b/334230214): Implement Vertex AI Prompt Management.
    print(
        f"""Simulating prompt creation:
  Display Name: {display_name}
  Model: {model}
  Content: {content}
  System Instruction: {system_instruction}
  Project ID: {project_id}
  Location ID: {location_id}"""
    )


def read_vertex_prompt(
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
    if project_id and location_id:
        vertexai.init(project=project_id, location=location_id)
    elif project_id:
        vertexai.init(project=project_id)

    # TODO(b/334230214): Implement Vertex AI Prompt Management.
    print(
        f"""Simulating reading prompt with ID: {prompt_id}
  Project ID: {project_id}
  Location ID: {location_id}"""
    )
    # Simulate a prompt response
    return {
        "id": prompt_id,
        "display_name": f"Simulated Prompt {prompt_id}",
        "content": f"Simulated content for {prompt_id}",
        "system_instruction": f"Simulated system instruction for {prompt_id}",
        "model": "gemini-pro",
    }


def update_vertex_prompt(
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
    if project_id and location_id:
        vertexai.init(project=project_id, location=location_id)
    elif project_id:
        vertexai.init(project=project_id)

    # TODO(b/334230214): Implement Vertex AI Prompt Management.
    print(
        f"""Simulating prompt update for ID: {prompt_id}
  New Content: {content}
  New System Instruction: {system_instruction}
  New Model: {model}
  Project ID: {project_id}
  Location ID: {location_id}"""
    )


def delete_vertex_prompt(
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
    if project_id and location_id:
        vertexai.init(project=project_id, location=location_id)
    elif project_id:
        vertexai.init(project=project_id)

    # TODO(b/334230214): Implement Vertex AI Prompt Management.
    print(
        f"""Simulating prompt deletion for ID: {prompt_id}
  Project ID: {project_id}
  Location ID: {location_id}"""
    )


def list_vertex_prompts(
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
    if project_id and location_id:
        vertexai.init(project=project_id, location=location_id)
    elif project_id:
        vertexai.init(project=project_id)

    # TODO(b/334230214): Implement Vertex AI Prompt Management.
    print(
        f"""Simulating listing prompts:
  Display Name Filter: {display_name}
  Page Size: {page_size}
  Project ID: {project_id}
  Location ID: {location_id}"""
    )
    # Simulate a list of prompt responses
    return [
        {
            "id": f"simulated-id-{i}",
            "display_name": f"Simulated Prompt {i}",
            "content": f"Simulated content {i}",
            "system_instruction": f"Simulated system instruction {i}",
            "model": "gemini-pro",
        }
        for i in range(page_size)
    ]

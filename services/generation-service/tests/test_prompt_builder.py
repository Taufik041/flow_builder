from unittest.mock import patch

from prompt_builder import build_system_prompt, build_user_message


def test_build_system_prompt_includes_chunks():
    chunks = [
        {"source": "knowledge_base", "title": "Test Section", "text": "Some rule here"}
    ]
    with patch("prompt_builder.load_examples", return_value="## Example\n```\n{}\n```"):
        prompt = build_system_prompt(chunks)
    assert "Some rule here" in prompt
    assert "knowledge_base" in prompt
    assert "CRITICAL RULES" in prompt
    assert "TODO PLACEHOLDERS" in prompt


def test_build_system_prompt_empty_chunks():
    with patch("prompt_builder.load_examples", return_value=""):
        prompt = build_system_prompt([])
    assert "KNOWLEDGE BASE" in prompt


def test_build_user_message_text_only():
    msg = build_user_message("Build a login form")
    assert "Build a login form" in msg
    assert "Generate" in msg


def test_build_user_message_with_extracted_text():
    msg = build_user_message("Build this form", extracted_text="Name: ___\nDOB: ___")
    assert "Name: ___" in msg
    assert "Build this form" in msg
    assert "extracted from uploaded file" in msg


def test_build_user_message_no_extracted_text():
    msg = build_user_message("Simple form", extracted_text=None)
    assert "extracted" not in msg

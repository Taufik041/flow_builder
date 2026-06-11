from chunker import chunk_code_file, chunk_markdown


def test_chunk_markdown_by_headers():
    text = """# Title

## Section One

This is the content of section one with enough characters to pass the minimum.

## Section Two

This is the content of section two with enough characters to pass the minimum.
"""
    chunks = chunk_markdown(text, "test_source")
    assert len(chunks) == 2
    assert chunks[0]["title"] == "Section One"
    assert chunks[1]["title"] == "Section Two"
    assert all(c["source"] == "test_source" for c in chunks)


def test_chunk_markdown_skips_tiny_sections():
    text = """## Tiny

x

## Real Section

This is a real section with enough content to be included in the chunks list.
"""
    chunks = chunk_markdown(text, "test")
    assert len(chunks) == 1
    assert chunks[0]["title"] == "Real Section"


def test_chunk_code_file_small():
    code = "def hello():\n    return 'world'"
    chunks = chunk_code_file(code, "test_code")
    assert len(chunks) == 1
    assert chunks[0]["text"] == code


def test_chunk_code_file_large():
    code = "x" * 7000
    chunks = chunk_code_file(code, "big_code", max_chars=3000)
    assert len(chunks) == 3
    assert chunks[0]["title"] == "big_code_part_0"

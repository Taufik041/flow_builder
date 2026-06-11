import re


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split markdown by ## headers - each section becomes one chunk."""
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section or len(section) < 50:
            continue
        # extract section title
        title_match = re.match(r"##\s+(.+)", section)
        title = title_match.group(1) if title_match else "untitled"
        chunks.append(
            {
                "text": section,
                "source": source,
                "title": title,
            }
        )
    return chunks


def chunk_code_file(text: str, source: str, max_chars: int = 3000) -> list[dict]:
    """Code/JSON examples are stored as full files if small, else split by size."""
    if len(text) <= max_chars:
        return [{"text": text, "source": source, "title": source}]

    chunks = []
    for i in range(0, len(text), max_chars):
        chunks.append(
            {
                "text": text[i : i + max_chars],
                "source": source,
                "title": f"{source}_part_{i // max_chars}",
            }
        )
    return chunks

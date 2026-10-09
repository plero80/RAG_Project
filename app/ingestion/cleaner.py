import re
import unicodedata


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\x00", "")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Fix hyphenated words split across lines
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Collapse horizontal whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces surrounding line breaks
    text = re.sub(r" *\n *", "\n", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_pages(pages: list[dict]) -> list[dict]:
    cleaned_pages = []

    for page in pages:
        cleaned_text = clean_text(page["text"])

        if not cleaned_text:
            continue

        cleaned_blocks = []

        for block in page.get("blocks") or []:
            block_text = clean_text(block["text"])

            if not block_text:
                continue

            cleaned_blocks.append({
                **block,
                "text": block_text,
            })

        cleaned_pages.append({
            **page,
            "text": cleaned_text,
            "blocks": cleaned_blocks,
        })

    return cleaned_pages
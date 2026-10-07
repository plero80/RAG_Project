import re
import unicodedata


def clean_text(text: str) -> str:
    # Normalize weird Unicode representations
    text = unicodedata.normalize("NFKC", text)

    # Remove NULL characters
    text = text.replace("\x00", "")

    # Normalize Windows/Mac newlines
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Fix words broken by PDF line wrapping:
    #
    # "inter-\nnational"
    #
    # becomes:
    #
    # "international"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Replace multiple spaces/tabs with one space
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Don't allow huge amounts of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


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

        cleaned_pages.append({
            "document": page["document"],
            "page": page["page"],
            "text": cleaned_text
        })

    return cleaned_pages
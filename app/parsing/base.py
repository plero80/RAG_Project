from abc import ABC,abstractmethod
import hashlib
from pathlib import Path

class DocumentParser(ABC):

    document_id: str = ""

    def DocumentParser(path: Path):
        document_id = generate_document_id(path)

    @abstractmethod
    def parse(self, path: str) -> str:
        pass

    

def generate_document_id(path: Path) -> str:
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(lambda: file.read(8192), b""):
            sha256.update(block)

    return sha256.hexdigest()
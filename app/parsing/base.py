from abc import ABC,abstractmethod
import hashlib
from pathlib import Path

class DocumentParser(ABC):


    @abstractmethod
    def parse(self, file_path: str) -> list[dict]:
        pass

    

def generate_document_id(path: str) -> str:
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(lambda: file.read(8192), b""):
            sha256.update(block)

    return sha256.hexdigest()
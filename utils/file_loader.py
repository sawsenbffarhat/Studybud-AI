import fitz  # PyMuPDF
from pathlib import Path


class PDFLoader:
    """
    Responsible for loading PDF files
    and extracting plain text.
    """

    def extract_pages(self, pdf_path: str) -> list:
        """
        Extract text page by page.

        Returns:
            list[dict]: [{"page": 1, "text": "..."}, ...]
            (pages without text are skipped, page numbers start at 1)
        """

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")

        pages = []

        with fitz.open(pdf_path) as document:

            for number, page in enumerate(document, start=1):

                text = page.get_text().strip()

                if text:
                    pages.append({"page": number, "text": text})

            self.page_count = len(document)

        return pages

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file as one string.
        """

        return "\n".join(
            page["text"] for page in self.extract_pages(pdf_path)
        )

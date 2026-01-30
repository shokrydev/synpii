"""Output formatters for different benchmark formats."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, TextIO, Union

from synpii.core.types import GeneratedDocument, Annotation


class OutputFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format_document(self, doc: GeneratedDocument) -> str:
        """Format a single document.

        Args:
            doc: Document to format.

        Returns:
            Formatted string representation.
        """
        pass

    def format_documents(self, docs: List[GeneratedDocument]) -> str:
        """Format multiple documents.

        Args:
            docs: List of documents.

        Returns:
            Formatted string representation.
        """
        return "\n".join(self.format_document(doc) for doc in docs)

    def write(
        self,
        docs: List[GeneratedDocument],
        output: Union[str, Path, TextIO],
    ) -> None:
        """Write documents to file or stream.

        Args:
            docs: Documents to write.
            output: File path or file-like object.
        """
        content = self.format_documents(docs)

        if isinstance(output, (str, Path)):
            Path(output).write_text(content, encoding="utf-8")
        else:
            output.write(content)


class JSONLFormatter(OutputFormatter):
    """Format documents as JSON Lines (one JSON object per line).

    Output format:
    {"id": "doc_001", "text": "...", "annotations": [...]}
    {"id": "doc_002", "text": "...", "annotations": [...]}
    """

    def format_document(self, doc: GeneratedDocument) -> str:
        """Format document as JSON line."""
        return json.dumps(doc.to_dict(), ensure_ascii=False)

    def format_documents(self, docs: List[GeneratedDocument]) -> str:
        """Format documents as JSONL."""
        return "\n".join(self.format_document(doc) for doc in docs)


class CoNLLFormatter(OutputFormatter):
    """Format documents in CoNLL-style format for NER.

    Output format (BIO tagging):
    TOKEN    TAG
    Hans     B-PERSON
    Müller   I-PERSON
    wohnt    O
    in       O
    Berlin   B-LOCATION

    Empty line between documents.
    """

    def __init__(self, tag_scheme: str = "BIO"):
        """Initialize CoNLL formatter.

        Args:
            tag_scheme: Tagging scheme ('BIO', 'BIOES', or 'IO').
        """
        self.tag_scheme = tag_scheme

    def format_document(self, doc: GeneratedDocument) -> str:
        """Format document in CoNLL format."""
        lines = [f"# doc_id: {doc.id}"]

        # Tokenize text (simple whitespace tokenization)
        tokens = self._tokenize(doc.text)

        # Assign tags to tokens
        tagged = self._assign_tags(tokens, doc.annotations)

        for token, tag in tagged:
            lines.append(f"{token}\t{tag}")

        return "\n".join(lines)

    def _tokenize(self, text: str) -> List[tuple]:
        """Simple tokenization with offset tracking.

        Returns list of (token, start, end) tuples.
        """
        tokens = []
        current_start = 0
        current_token = ""

        for i, char in enumerate(text):
            if char.isspace():
                if current_token:
                    tokens.append((
                        current_token,
                        current_start,
                        current_start + len(current_token)
                    ))
                    current_token = ""
                current_start = i + 1
            else:
                if not current_token:
                    current_start = i
                current_token += char

        if current_token:
            tokens.append((
                current_token,
                current_start,
                current_start + len(current_token)
            ))

        return tokens

    def _assign_tags(
        self,
        tokens: List[tuple],
        annotations: List[Annotation],
    ) -> List[tuple]:
        """Assign BIO tags to tokens based on annotations."""
        tagged = []

        for token, start, end in tokens:
            tag = "O"

            # Check if token overlaps with any annotation
            for ann in annotations:
                if self._overlaps(start, end, ann.start, ann.end):
                    # Determine B or I tag
                    if start == ann.start or not self._continues_entity(
                        tagged, ann.entity_type
                    ):
                        tag = f"B-{ann.entity_type}"
                    else:
                        tag = f"I-{ann.entity_type}"
                    break

            tagged.append((token, tag))

        return tagged

    def _overlaps(self, s1: int, e1: int, s2: int, e2: int) -> bool:
        """Check if two spans overlap."""
        return not (e1 <= s2 or e2 <= s1)

    def _continues_entity(
        self,
        tagged: List[tuple],
        entity_type: str,
    ) -> bool:
        """Check if the previous token was the same entity type."""
        if not tagged:
            return False
        prev_tag = tagged[-1][1]
        return prev_tag.endswith(entity_type)


class PresidioFormatter(OutputFormatter):
    """Format documents for Presidio evaluation.

    Output format (JSON):
    {
        "documents": [
            {
                "full_text": "...",
                "spans": [
                    {"start": 0, "end": 10, "entity_type": "PERSON"},
                    ...
                ]
            }
        ]
    }
    """

    def format_document(self, doc: GeneratedDocument) -> str:
        """Format single document (returns JSON)."""
        return json.dumps({
            "full_text": doc.text,
            "spans": [
                {
                    "start": ann.start,
                    "end": ann.end,
                    "entity_type": ann.entity_type,
                }
                for ann in doc.annotations
            ],
        }, ensure_ascii=False)

    def format_documents(self, docs: List[GeneratedDocument]) -> str:
        """Format as Presidio evaluation JSON."""
        return json.dumps({
            "documents": [
                {
                    "full_text": doc.text,
                    "spans": [
                        {
                            "start": ann.start,
                            "end": ann.end,
                            "entity_type": ann.entity_type,
                        }
                        for ann in doc.annotations
                    ],
                }
                for doc in docs
            ],
        }, ensure_ascii=False, indent=2)


class HuggingFaceFormatter(OutputFormatter):
    """Format documents for HuggingFace datasets.

    Output format (JSONL with HF-compatible structure):
    {"tokens": ["Hans", "Müller", "..."], "ner_tags": ["B-PERSON", "I-PERSON", ...]}
    """

    def format_document(self, doc: GeneratedDocument) -> str:
        """Format document for HuggingFace."""
        # Tokenize
        tokens = []
        tags = []
        current_pos = 0

        # Simple word tokenization
        for word in doc.text.split():
            tokens.append(word)

            # Find position in original text
            pos = doc.text.find(word, current_pos)
            end_pos = pos + len(word)

            # Check if this token is part of an entity
            tag = "O"
            for ann in doc.annotations:
                if pos >= ann.start and end_pos <= ann.end:
                    if pos == ann.start:
                        tag = f"B-{ann.entity_type}"
                    else:
                        tag = f"I-{ann.entity_type}"
                    break

            tags.append(tag)
            current_pos = end_pos

        return json.dumps({
            "id": doc.id,
            "tokens": tokens,
            "ner_tags": tags,
        }, ensure_ascii=False)

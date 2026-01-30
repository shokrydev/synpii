"""Dataset builder for generating benchmark datasets."""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Any, TYPE_CHECKING

from synpii.core.types import GeneratedDocument
from synpii.output.formats import JSONLFormatter, CoNLLFormatter, PresidioFormatter

if TYPE_CHECKING:
    from synpii import SynPII


class DatasetBuilder:
    """Build datasets of synthetic PII documents.

    Supports:
    - Train/val/test splits
    - Adversarial rate control
    - Multiple output formats
    - Reproducible generation with seeds

    Example:
        from synpii import SynPII
        from synpii.output import DatasetBuilder

        synpii = SynPII(preset="clinical_de", seed=42)
        builder = DatasetBuilder(synpii)

        paths = builder.build(
            count=1000,
            adversarial_rate=0.3,
            output_path="datasets/clinical_1k",
            format="jsonl",
            splits={"train": 0.8, "val": 0.1, "test": 0.1},
        )
    """

    FORMATTERS = {
        "jsonl": JSONLFormatter,
        "conll": CoNLLFormatter,
        "presidio": PresidioFormatter,
    }

    def __init__(self, synpii: "SynPII"):
        """Initialize dataset builder.

        Args:
            synpii: SynPII instance for document generation.
        """
        self.synpii = synpii

    def build(
        self,
        count: int = 100,
        adversarial_rate: float = None,
        output_path: str = None,
        format: str = "jsonl",
        splits: Dict[str, float] = None,
    ) -> List[GeneratedDocument]:
        """Build a dataset of documents.

        Args:
            count: Total number of documents to generate.
            adversarial_rate: Override perturbation rate (uses preset if None).
            output_path: Path to save dataset (returns only if None).
            format: Output format ('jsonl', 'conll', 'presidio').
            splits: Optional dict of split ratios (e.g., {"train": 0.8, "test": 0.2}).

        Returns:
            List of generated documents.
        """
        documents = []

        # Generate documents
        for i in range(count):
            doc = self.synpii.generate_document(doc_id=f"doc_{i:05d}")
            documents.append(doc)

        # Verify annotations
        for doc in documents:
            if not doc.verify_annotations():
                # Log warning but continue
                pass

        # Save if output path provided
        if output_path:
            self._save_dataset(documents, output_path, format, splits)

        return documents

    def _save_dataset(
        self,
        documents: List[GeneratedDocument],
        output_path: str,
        format: str,
        splits: Dict[str, float] = None,
    ) -> Dict[str, Path]:
        """Save dataset to disk.

        Args:
            documents: Documents to save.
            output_path: Base output path.
            format: Output format.
            splits: Optional split ratios.

        Returns:
            Dict mapping split names to file paths.
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        formatter_cls = self.FORMATTERS.get(format, JSONLFormatter)
        formatter = formatter_cls()

        paths = {}

        if splits:
            # Split documents
            split_docs = self._split_documents(documents, splits)

            for split_name, docs in split_docs.items():
                file_path = output_dir / f"{split_name}.{self._get_extension(format)}"
                formatter.write(docs, file_path)
                paths[split_name] = file_path
        else:
            # Single file
            file_path = output_dir / f"data.{self._get_extension(format)}"
            formatter.write(documents, file_path)
            paths["all"] = file_path

        # Save metadata
        metadata_path = output_dir / "metadata.json"
        self._save_metadata(documents, metadata_path, splits)
        paths["metadata"] = metadata_path

        return paths

    def _split_documents(
        self,
        documents: List[GeneratedDocument],
        splits: Dict[str, float],
    ) -> Dict[str, List[GeneratedDocument]]:
        """Split documents according to ratios.

        Args:
            documents: Documents to split.
            splits: Dict of split name to ratio.

        Returns:
            Dict mapping split names to document lists.
        """
        # Normalize ratios
        total = sum(splits.values())
        normalized = {k: v / total for k, v in splits.items()}

        # Shuffle documents
        shuffled = documents.copy()
        random.shuffle(shuffled)

        result = {}
        start = 0

        for split_name, ratio in normalized.items():
            count = int(len(shuffled) * ratio)
            if split_name == list(splits.keys())[-1]:
                # Last split gets remainder
                result[split_name] = shuffled[start:]
            else:
                result[split_name] = shuffled[start:start + count]
                start += count

        return result

    def _save_metadata(
        self,
        documents: List[GeneratedDocument],
        path: Path,
        splits: Dict[str, float] = None,
    ) -> None:
        """Save dataset metadata."""
        # Collect statistics
        entity_counts = {}
        template_counts = {}

        for doc in documents:
            # Count by template type
            template_counts[doc.template_type] = template_counts.get(doc.template_type, 0) + 1

            # Count by entity type
            for ann in doc.annotations:
                entity_counts[ann.entity_type] = entity_counts.get(ann.entity_type, 0) + 1

        metadata = {
            "total_documents": len(documents),
            "entity_counts": entity_counts,
            "template_counts": template_counts,
            "preset": self.synpii.preset,
            "splits": splits,
        }

        path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    def _get_extension(self, format: str) -> str:
        """Get file extension for format."""
        extensions = {
            "jsonl": "jsonl",
            "conll": "conll",
            "presidio": "json",
        }
        return extensions.get(format, "txt")

    def build_adversarial(
        self,
        count: int = 100,
        perturbation_rate: float = 0.5,
        output_path: str = None,
    ) -> List[GeneratedDocument]:
        """Build an adversarial dataset with high perturbation rate.

        Convenience method for creating challenging test sets.

        Args:
            count: Number of documents.
            perturbation_rate: Rate of perturbation (0.0-1.0).
            output_path: Optional output path.

        Returns:
            List of perturbed documents.
        """
        return self.build(
            count=count,
            adversarial_rate=perturbation_rate,
            output_path=output_path,
        )

    def build_evaluation_set(
        self,
        count: int = 500,
        output_path: str = None,
    ) -> Dict[str, List[GeneratedDocument]]:
        """Build a structured evaluation set.

        Creates:
        - clean: Unperturbed documents
        - adversarial_low: 20% perturbation
        - adversarial_high: 50% perturbation

        Args:
            count: Documents per category.
            output_path: Base output path.

        Returns:
            Dict mapping category names to document lists.
        """
        result = {}

        # Save original perturbation config
        original_rate = self.synpii.config.get("perturbation_rate", 0)

        # Clean set
        self.synpii.config["perturbation_rate"] = 0.0
        result["clean"] = self.build(count=count)

        # Low adversarial
        self.synpii.config["perturbation_rate"] = 0.2
        result["adversarial_low"] = self.build(count=count)

        # High adversarial
        self.synpii.config["perturbation_rate"] = 0.5
        result["adversarial_high"] = self.build(count=count)

        # Restore original config
        self.synpii.config["perturbation_rate"] = original_rate

        # Save if path provided
        if output_path:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            formatter = JSONLFormatter()
            for name, docs in result.items():
                file_path = output_dir / f"{name}.jsonl"
                formatter.write(docs, file_path)

        return result

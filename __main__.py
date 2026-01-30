#!/usr/bin/env python3
"""CLI interface for SynPII.

Usage:
    python -m synpii generate --preset clinical_de --count 100 --output data.jsonl
    python -m synpii entity --type PERSON --count 10
    python -m synpii list-presets
    python -m synpii list-entities
"""

import argparse
import json
import sys


def cmd_generate(args):
    """Generate documents."""
    from synpii import SynPII

    synpii = SynPII(preset=args.preset, seed=args.seed)

    print(f"Generating {args.count} documents with preset '{args.preset}'...", file=sys.stderr)

    docs = []
    for i in range(args.count):
        doc = synpii.generate_document(doc_id=f"doc_{i:05d}")
        docs.append(doc)

        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{args.count}", file=sys.stderr)

    print(f"Generated {len(docs)} documents", file=sys.stderr)

    # Output
    if args.output:
        from pathlib import Path
        output_path = Path(args.output)

        if args.format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for doc in docs:
                    f.write(json.dumps(doc.to_dict(), ensure_ascii=False) + "\n")
        elif args.format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([doc.to_dict() for doc in docs], f, ensure_ascii=False, indent=2)

        print(f"Saved to {output_path}", file=sys.stderr)
    else:
        # Print to stdout
        for doc in docs:
            print(json.dumps(doc.to_dict(), ensure_ascii=False))


def cmd_entity(args):
    """Generate entities."""
    from synpii import SynPII

    synpii = SynPII(preset="clinical_de", seed=args.seed)

    print(f"Generating {args.count} {args.type} entities...", file=sys.stderr)

    for i in range(args.count):
        entity = synpii.generate_entity(args.type)
        print(json.dumps(entity.to_dict(), ensure_ascii=False))


def cmd_list_presets(args):
    """List available presets."""
    from synpii import SynPII

    print("Available presets:")
    for name, config in SynPII.PRESETS.items():
        entity_count = len(config.get("entity_types", []))
        pert_rate = config.get("perturbation_rate", 0)
        print(f"  {name}:")
        print(f"    Entity types: {entity_count}")
        print(f"    Perturbation rate: {pert_rate}")
        print(f"    Templates: {config.get('templates', 'clinical')}")


def cmd_list_entities(args):
    """List available entity types."""
    from synpii import SynPII

    synpii = SynPII(preset="full_german")

    print("Available entity types:")
    for entity_type in synpii.generators.available_types:
        # Generate sample
        try:
            entity = synpii.generate_entity(entity_type)
            print(f"  {entity_type}: e.g., '{entity.value}'")
        except Exception as e:
            print(f"  {entity_type}: (error generating sample)")


def cmd_test(args):
    """Run test suite."""
    from synpii.test_synpii import main
    sys.exit(main())


def main():
    parser = argparse.ArgumentParser(
        description="SynPII: Synthetic PII Generation Library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate documents")
    gen_parser.add_argument("--preset", default="clinical_de",
                            help="Generation preset (default: clinical_de)")
    gen_parser.add_argument("--count", type=int, default=10,
                            help="Number of documents (default: 10)")
    gen_parser.add_argument("--output", "-o", help="Output file path")
    gen_parser.add_argument("--format", choices=["jsonl", "json"], default="jsonl",
                            help="Output format (default: jsonl)")
    gen_parser.add_argument("--seed", type=int, help="Random seed")
    gen_parser.set_defaults(func=cmd_generate)

    # entity command
    ent_parser = subparsers.add_parser("entity", help="Generate individual entities")
    ent_parser.add_argument("--type", "-t", required=True,
                            help="Entity type (e.g., PERSON, DE_KVNR)")
    ent_parser.add_argument("--count", type=int, default=1,
                            help="Number of entities (default: 1)")
    ent_parser.add_argument("--seed", type=int, help="Random seed")
    ent_parser.set_defaults(func=cmd_entity)

    # list-presets command
    presets_parser = subparsers.add_parser("list-presets", help="List available presets")
    presets_parser.set_defaults(func=cmd_list_presets)

    # list-entities command
    entities_parser = subparsers.add_parser("list-entities", help="List available entity types")
    entities_parser.set_defaults(func=cmd_list_entities)

    # test command
    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.set_defaults(func=cmd_test)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

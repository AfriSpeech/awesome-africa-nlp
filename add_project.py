#!/usr/bin/env python3
"""Parse a project submission and add it to README.md.

Usage:
    # From arguments:
    python add_project.py \
        --name "masakhane-mt" \
        --url "https://github.com/masakhane-io/masakhane-mt" \
        --region "Pan-African" \
        --language "yor,hau,ibo,swa" \
        --language-name "Yoruba,Hausa,Igbo,Swahili" \
        --description "Machine translation for 38+ African languages using OpenNMT." \
        --type "Machine Translation"

    # From a JSON file (e.g. parsed from GitHub issue):
    python add_project.py --json submission.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

README = Path(__file__).parent / "README.md"

# Map issue template region values to README section headers
REGION_MAP = {
    "Pan-African": "Pan-African / Multilingual",
    "West Africa": "West Africa",
    "East Africa": "East Africa",
    "North Africa": "North Africa",
    "Southern Africa": "Southern Africa",
    "Central Africa": "Central Africa",
    "Speech & Audio (cross-region)": "Speech & Audio",
    "Datasets & Benchmarks (cross-region)": "Datasets & Benchmarks",
    "Tools & Libraries (cross-region)": "Tools & Libraries",
}


def find_section_end(readme: str, section_header: str) -> int:
    """Find the end position of a section (before the next ## header)."""
    idx = readme.find(section_header)
    if idx == -1:
        return -1

    # Find the next ## after this section
    next_section = re.search(r"\n## ", readme[idx + len(section_header) :])
    if next_section:
        return idx + len(section_header) + next_section.start()
    return len(readme)


def build_row(name: str, url: str, languages: str, description: str) -> str:
    """Build a markdown table row for the Pan-African section."""
    repo_short = url.rstrip("/").split("/")[-1]
    return f"| [{repo_short}]({url}) | {languages} | {description} |"


def build_list_item(name: str, url: str, description: str) -> str:
    """Build a markdown list item for language-specific sections."""
    return f"- [{name}]({url}) - {description}"


def detect_section_format(readme: str, section_start: int, section_end: int) -> str:
    """Detect whether a section uses table or list format."""
    section_content = readme[section_start:section_end]
    if "| :" in section_content or "| Project" in section_content:
        return "table"
    return "list"


def add_to_pan_african(readme: str, row: str) -> str:
    """Add a project to the Pan-African table section."""
    section_header = "## Pan-African / Multilingual"
    idx = readme.find(section_header)
    if idx == -1:
        print(f"Error: Section '{section_header}' not found")
        sys.exit(1)

    # Find the separator row
    sep_match = re.search(r"\| :-- \| :-- \| :-- \|", readme[idx:])
    if not sep_match:
        print("Error: Could not find table separator in Pan-African section")
        sys.exit(1)

    insert_idx = idx + sep_match.end()
    newline = readme.find("\n", insert_idx)
    if newline != -1:
        insert_idx = newline

    return readme[:insert_idx] + "\n" + row + readme[insert_idx:]


def add_to_language_section(readme: str, region: str, language_name: str, item: str) -> str:
    """Add a project to a language-specific section."""
    section_header = f"## {region}"
    idx = readme.find(section_header)
    if idx == -1:
        print(f"Error: Section '{section_header}' not found")
        sys.exit(1)

    section_end = find_section_end(readme, section_header)

    # Find the language subsection (e.g. ### Yoruba)
    lang_pattern = re.compile(r"### " + re.escape(language_name), re.IGNORECASE)
    lang_match = lang_pattern.search(readme[idx:section_end])

    if lang_match:
        # Find end of this language subsection (next ### or end of section)
        lang_start = idx + lang_match.end()
        next_lang = re.search(r"\n### ", readme[lang_start:section_end])
        if next_lang:
            insert_idx = lang_start + next_lang.start()
        else:
            insert_idx = section_end
    else:
        # Language not found - find insertion point before next ### or at section end
        next_lang = re.search(r"\n### ", readme[idx + len(section_header) :section_end])
        if next_lang:
            insert_idx = idx + len(section_header) + next_lang.start()
        else:
            insert_idx = section_end

        # Add language subsection
        new_subsection = f"""
### {language_name}

{item}
"""
        return readme[:insert_idx] + new_subsection + readme[insert_idx:]

    # Check format of existing list
    section_content = readme[idx:section_end]
    if "| :" in section_content:
        # Table format - not used for language sections, but handle gracefully
        pass

    # Insert the list item
    return readme[:insert_idx] + "\n" + item + readme[insert_idx:]


def add_to_cross_region(readme: str, section_name: str, row: str) -> str:
    """Add a project to a cross-region section (Speech, Datasets, Tools)."""
    section_header = f"## {section_name}"
    idx = readme.find(section_header)
    if idx == -1:
        print(f"Error: Section '{section_header}' not found")
        sys.exit(1)

    # Find the separator row
    sep_match = re.search(r"\| :-- \| :-- \| :-- \|", readme[idx:])
    if not sep_match:
        print(f"Error: Could not find table separator in {section_name} section")
        sys.exit(1)

    insert_idx = idx + sep_match.end()
    newline = readme.find("\n", insert_idx)
    if newline != -1:
        insert_idx = newline

    return readme[:insert_idx] + "\n" + row + readme[insert_idx:]


def add_project(
    name: str,
    url: str,
    region: str,
    language: str,
    language_name: str,
    description: str,
    type_: str = "",
) -> None:
    """Add a project entry to the README."""
    readme = README.read_text(encoding="utf-8")

    readme_section = REGION_MAP.get(region)
    if not readme_section:
        print(f"Error: Unknown region '{region}'. Must be one of: {list(REGION_MAP.keys())}")
        sys.exit(1)

    if readme_section == "Pan-African / Multilingual":
        row = build_row(name, url, language_name, description)
        readme = add_to_pan_african(readme, row)
    elif readme_section in ("Speech & Audio", "Datasets & Benchmarks", "Tools & Libraries"):
        row = build_row(name, url, language_name, description)
        readme = add_to_cross_region(readme, readme_section, row)
    else:
        item = build_list_item(name, url, description)
        readme = add_to_language_section(readme, readme_section, language_name, item)

    README.write_text(readme, encoding="utf-8")
    print(f"Added '{name}' under {language_name} ({readme_section})")


def main():
    parser = argparse.ArgumentParser(description="Add a project to README.md")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--url", help="GitHub URL")
    parser.add_argument("--region", help="Region")
    parser.add_argument("--language", help="ISO 639-3 codes (comma-separated)")
    parser.add_argument("--language-name", help="Language names (comma-separated)")
    parser.add_argument("--description", help="Description")
    parser.add_argument("--type", help="Project type", default="")
    parser.add_argument("--json", help="Path to JSON file with submission data")

    args = parser.parse_args()

    if args.json:
        data = json.loads(Path(args.json).read_text())
    elif args.name and args.url and args.region and args.language_name and args.description:
        data = {
            "name": args.name,
            "url": args.url,
            "region": args.region,
            "language": args.language or "",
            "language_name": args.language_name,
            "description": args.description,
            "type": args.type or "",
        }
    else:
        print("Error: Provide --json or all required arguments (--name, --url, --region, --language-name, --description)")
        sys.exit(1)

    add_project(
        name=data.get("name", ""),
        url=data.get("url", ""),
        region=data.get("region", ""),
        language=data.get("language", ""),
        language_name=data.get("language_name", ""),
        description=data.get("description", ""),
        type_=data.get("type", ""),
    )


if __name__ == "__main__":
    main()

import subprocess
import re
from datetime import datetime
import sys

# Mapping from conventional commit types to changelog sections
COMMIT_TYPE_MAP = {
    "feat": "🚀 Features",
    "fix": "🐛 Bug Fixes",
    "docs": "📚 Documentation",
    "style": "🎨 Styles",
    "refactor": "🔨 Code Refactoring",
    "perf": "⚡ Performance Improvements",
    "test": "✅ Testing",
    "build": "📦 Build System",
    "ci": "🤖 Continuous Integration",
}


def get_previous_tag(current_tag):
    """Gets the tag before the current one."""
    try:
        # Get all tags sorted by version descending
        tags_str = subprocess.check_output(
            ["git", "tag", "--sort=-v:refname"], text=True, stderr=subprocess.PIPE
        ).strip()
        tags = tags_str.split("\n")

        # Find the index of the current tag
        try:
            current_index = tags.index(current_tag)
            if current_index + 1 < len(tags):
                return tags[current_index + 1]
        except ValueError:
            # If current tag is not in the list (e.g., a new tag not yet pushed)
            # return the latest known tag.
            return tags[0] if tags else None

    except subprocess.CalledProcessError:
        return None  # No tags found


def get_commits_since_tag(tag):
    """Gets commit messages since the given tag."""
    if not tag:
        return []
    # Using a simple format: just the subject line
    command = ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"]
    try:
        commits = (
            subprocess.check_output(command, text=True, encoding="utf-8")
            .strip()
            .split("\n")
        )
        # Filter out empty lines that might result from the split
        return [commit for commit in commits if commit]
    except subprocess.CalledProcessError:
        return []


def parse_commits(commits):
    """Parses commits and groups them by their conventional commit type."""
    categorized_commits = {}
    # Regex to capture type, scope (optional), and subject
    commit_pattern = re.compile(
        r"^(?P<type>\w+)(?:\((?P<scope>.*)\))?!?: (?P<subject>.+)$"
    )

    for commit_msg in commits:
        match = commit_pattern.match(commit_msg)
        if not match:
            continue

        commit_type = match.group("type")
        subject = match.group("subject").strip()

        category_title = COMMIT_TYPE_MAP.get(commit_type)
        if category_title:
            if category_title not in categorized_commits:
                categorized_commits[category_title] = []
            categorized_commits[category_title].append(subject)

    return categorized_commits


def generate_changelog_text(categorized_commits, new_version):
    """Generates the changelog content in Markdown format."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Start with the header for the new version
    changelog_parts = [f"## {new_version} ({today})\n"]

    if not categorized_commits:
        changelog_parts.append("No notable changes for this version.")
        return "\n".join(changelog_parts)

    # Add commits for each category
    for category, messages in categorized_commits.items():
        changelog_parts.append(f"### {category}\n")
        for msg in messages:
            changelog_parts.append(f"- {msg}")
        changelog_parts.append("")  # Add a newline for spacing

    return "\n".join(changelog_parts)


def update_main_changelog(new_content, changelog_file="CHANGELOG.md"):
    """Prepends new content to the main CHANGELOG.md file."""
    existing_content = ""
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file."
    try:
        with open(changelog_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        print(f"'{changelog_file}' not found. A new file will be created.")

    # Remove old header if it exists to avoid duplication
    if existing_content.startswith("# Changelog"):
        # Find the first real entry (starts with '## v')
        first_entry_match = re.search(r"## v\d", existing_content)
        if first_entry_match:
            old_entries = existing_content[first_entry_match.start() :]
        else:
            old_entries = ""  # No previous versions found
    else:
        old_entries = existing_content

    full_content = f"{header}\n\n{new_content}\n\n{old_entries.strip()}"

    with open(changelog_file, "w", encoding="utf-8") as f:
        f.write(full_content)
    print(f"'{changelog_file}' has been updated.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_changelog.py <new_version_tag> [--update-file <filename>]"
        )
        sys.exit(1)

    new_version_tag = sys.argv[1]
    body_output_file = "changelog_body.md"

    previous_tag = get_previous_tag(new_version_tag)
    commits = get_commits_since_tag(previous_tag)

    if not commits:
        changelog_content = "No notable changes for this version."
    else:
        categorized = parse_commits(commits)
        changelog_content = generate_changelog_text(categorized, new_version_tag)

    # Write to the body file for the release
    with open(body_output_file, "w", encoding="utf-8") as f:
        f.write(changelog_content)
    print(f"Changelog body generated and saved to {body_output_file}")

    # If --update-file is passed, update the main changelog file
    if "--update-file" in sys.argv:
        main_changelog_file = "CHANGELOG.md"
        update_main_changelog(changelog_content, main_changelog_file)

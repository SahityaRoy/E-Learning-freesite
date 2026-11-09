import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIRECTORIES = ("assets", "images", "blogs", "courses", "Contributor")


def build_static_site(output_directory):
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PROJECT_ROOT / "templates", output_directory, dirs_exist_ok=True)

    for directory in STATIC_DIRECTORIES:
        source = PROJECT_ROOT / directory
        if source.exists():
            shutil.copytree(source, output_directory / directory, dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Export MVC templates and static assets for static hosting.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "build",
        help="Directory to receive the static site (default: build/).",
    )
    args = parser.parse_args()
    build_static_site(args.output)


if __name__ == "__main__":
    main()
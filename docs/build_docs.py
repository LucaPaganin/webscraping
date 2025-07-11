#!/usr/bin/env python3
"""
Documentation setup helper script.
This script helps set up and build the Sphinx documentation.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def install_requirements():
    """Install the documentation dependencies."""
    docs_dir = Path(__file__).parent.absolute()
    requirements_file = docs_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Error: Could not find {requirements_file}")
        return False
    
    print("Installing documentation dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error installing dependencies: {result.stderr}")
        return False
    
    print("Dependencies installed successfully.")
    return True

def build_docs(format="html"):
    """Build the documentation in the specified format."""
    docs_dir = Path(__file__).parent.absolute()
    
    # Determine the build command based on OS
    if os.name == "nt":  # Windows
        build_script = str(docs_dir / "make.bat")
        build_cmd = [build_script, format]
    else:  # Linux/Mac
        build_cmd = ["make", "-C", str(docs_dir), format]
    
    print(f"Building {format} documentation...")
    result = subprocess.run(build_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error building documentation: {result.stderr}")
        return False
    
    output_dir = docs_dir / "build" / format
    print(f"Documentation built successfully. Output is in {output_dir}")
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build Sphinx documentation")
    parser.add_argument(
        "--format", "-f", default="html", choices=["html", "pdf", "epub"],
        help="Output format for documentation (default: html)"
    )
    parser.add_argument(
        "--skip-install", "-s", action="store_true",
        help="Skip installing dependencies"
    )
    args = parser.parse_args()
    
    if not args.skip_install:
        if not install_requirements():
            return 1
    
    if not build_docs(args.format):
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

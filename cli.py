#!/usr/bin/env python3
"""
Command-line tool for file conversion and analysis operations.

This tool provides two main commands:
- convert: Convert file content (e.g., to uppercase)
- analyze: Analyze file content (e.g., count words, lines)
"""

import argparse
import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import CONFIG
from example_module import greet

def setup_logging():
    """Setup logging configuration for the CLI tool."""
    logging.basicConfig(
        level=getattr(logging, CONFIG["log_level"]),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(CONFIG["log_file"]),
            logging.StreamHandler()
        ]
    )

def convert_file(input_file, output_file=None, to_upper=False):
    """
    Convert file content.

    Args:
        input_file (str): Path to input file
        output_file (str, optional): Path to output file. If None, overwrites input file.
        to_upper (bool): Whether to convert to uppercase

    Raises:
        FileNotFoundError: If input file doesn't exist
        IOError: If file cannot be read or written
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if to_upper:
            content = content.upper()

        output_path = output_file if output_file else input_file

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logging.info(f"Successfully converted file: {input_file} -> {output_path}")
        print(f"File converted successfully: {output_path}")

    except FileNotFoundError:
        error_msg = f"Input file not found: {input_file}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    except IOError as e:
        error_msg = f"IO error during file conversion: {e}"
        logging.error(error_msg)
        raise IOError(error_msg)

def analyze_file(input_file):
    """
    Analyze file content and print statistics.

    Args:
        input_file (str): Path to file to analyze

    Raises:
        FileNotFoundError: If input file doesn't exist
        IOError: If file cannot be read
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.splitlines()
        words = content.split()
        chars = len(content)

        print(f"File Analysis: {input_file}")
        print(f"Lines: {len(lines)}")
        print(f"Words: {len(words)}")
        print(f"Characters: {chars}")

        logging.info(f"Analyzed file: {input_file} - {len(lines)} lines, {len(words)} words, {chars} chars")

    except FileNotFoundError:
        error_msg = f"Input file not found: {input_file}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    except IOError as e:
        error_msg = f"IO error during file analysis: {e}"
        logging.error(error_msg)
        raise IOError(error_msg)

def main():
    """Main entry point for the CLI tool."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting {CONFIG['app_name']} CLI v{CONFIG['version']}")

    parser = argparse.ArgumentParser(
        description=f"{CONFIG['app_name']} - Command-line tool for file operations",
        prog='cli'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert file content')
    convert_parser.add_argument('input_file', help='Input file path')
    convert_parser.add_argument('-o', '--output', help='Output file path (optional)')
    convert_parser.add_argument('--upper', action='store_true', help='Convert to uppercase')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze file content')
    analyze_parser.add_argument('input_file', help='File to analyze')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'convert':
            convert_file(args.input_file, args.output, args.upper)
        elif args.command == 'analyze':
            analyze_file(args.input_file)
    except (FileNotFoundError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
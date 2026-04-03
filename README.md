# My Python Application

A simple Flask web application with command-line tool, using clean project structure.

## Project Structure

- `main.py`: Entry point of the Flask application
- `cli.py`: Command-line tool using argparse
- `src/`: Source code modules
  - `__init__.py`: Package initialization
  - `example_module.py`: Example functions
- `templates/`: Jinja2 templates
  - `home.html`: Home page template
- `config.py`: Configuration settings
- `requirements.txt`: Python dependencies

## Setup

1. Ensure you have Python 3.7+ installed
2. Activate the virtual environment:
   ```bash
   # On Windows
   .venv\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Web Application

Run the Flask application using:

```bash
python main.py
```

Or with the virtual environment Python:

```bash
.venv\.venv\Scripts\python.exe main.py
```

The application will start a web server on `http://127.0.0.1:5000`

## Command-Line Tool

The CLI tool provides file conversion and analysis operations:

```bash
python cli.py --help
```

### Available Commands:

#### Analyze a file:
```bash
python cli.py analyze <filename>
```
Example:
```bash
python cli.py analyze sample.txt
```
Output: Lines, words, and character count

#### Convert a file:
```bash
python cli.py convert <input_file> [--upper] [-o <output_file>]
```
Examples:
```bash
# Convert to uppercase and overwrite
python cli.py convert sample.txt --upper

# Convert to uppercase and save to new file
python cli.py convert sample.txt --upper -o sample_upper.txt
```

## Routes

- `/`: Home page displaying app information
- `/health`: Health check endpoint returning JSON status

## Testing

You can test the routes by visiting:
- http://127.0.0.1:5000/ (home page)
- http://127.0.0.1:5000/health (health check)

The CLI tool includes comprehensive error handling for missing files and I/O errors.
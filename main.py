import logging
import sys
import os
from flask import Flask, render_template, jsonify

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import CONFIG
from example_module import greet, calculate, get_square

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, CONFIG["log_level"]),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(CONFIG["log_file"]),
            logging.StreamHandler()
        ]
    )

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """Home route that renders the home template."""
    return render_template('home.html',
                         title='Home',
                         app_name=CONFIG['app_name'],
                         version=CONFIG['version'])

@app.route("/healthz")
def health_check():
    return "OK", 200

@app.route('/health')
def health():
    """Health check route."""
    return jsonify({
        'status': 'healthy',
        'app_name': CONFIG['app_name'],
        'version': CONFIG['version']
    })

def main():
    """Main entry point - setup and run the Flask app."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting {CONFIG['app_name']} v{CONFIG['version']}")

    # Example usage of modules (for demonstration)
    greeting = greet("Flask App")
    logger.info(f"Greeting: {greeting}")

    result = calculate(10, 5)
    logger.info(f"10 + 5 = {result}")

    square = get_square(4)
    logger.info(f"Square of 4 = {square}")

    logger.info("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()

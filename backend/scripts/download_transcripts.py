import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REPO_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data" / "transcripts"

def download_transcripts(dest_dir: Path):
    """
    Clones or pulls the Lenny's Podcast transcripts repository.
    """
    logger.info(f"Target directory: {dest_dir}")
    
    if dest_dir.exists() and (dest_dir / ".git").exists():
        logger.info("Existing Git repository found. Pulling latest changes...")
        try:
            subprocess.run(
                ["git", "-C", str(dest_dir), "pull", "--ff-only"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Successfully pulled latest changes.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull repository: {e.stderr}")
            logger.warning("Continuing with existing stale data. If this is a problem, delete the directory and retry.")
    else:
        logger.info(f"Cloning repository from {REPO_URL}...")
        try:
            # We use depth 1 to save time/bandwidth since we just want the latest transcripts
            subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, str(dest_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Successfully cloned repository.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Download Lenny's Podcast transcripts.")
    parser.add_argument(
        "--dest", 
        type=str, 
        default=str(DEFAULT_DATA_DIR),
        help="Destination directory for the transcripts."
    )
    
    args = parser.parse_args()
    dest_path = Path(args.dest)
    
    # Ensure parent dir exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    download_transcripts(dest_path)

if __name__ == "__main__":
    main()

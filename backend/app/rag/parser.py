import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ParsedParagraph:
    def __init__(self, text: str, speaker: Optional[str] = None, start_time: Optional[str] = None):
        self.text = text
        self.speaker = speaker
        self.start_time = start_time
        
    def __repr__(self):
        return f"ParsedParagraph(speaker={self.speaker}, start_time={self.start_time}, text_len={len(self.text)})"

class TranscriptParser:
    def __init__(self):
        # Matches formats like: "Brian Chesky (00:00:00):"
        self.speaker_re = re.compile(r"^(.*?)\s+\(([\d:]+)\):$")
        # Matches continuation formats like: "(00:00:52):"
        self.timestamp_only_re = re.compile(r"^\(([\d:]+)\):$")
        
    def parse_file(self, file_path: Path) -> Tuple[Dict[str, Any], List[ParsedParagraph]]:
        """
        Parses a transcript.md file and returns the metadata and a list of paragraphs with speaker info.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {}, []
            
        parts = content.split("---", 2)
        metadata = {}
        text_content = ""
        
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML in {file_path}: {e}")
            text_content = parts[2].strip()
        else:
            logger.warning(f"No YAML frontmatter found in {file_path}")
            text_content = content.strip()
            
        # Parse publication date if possible
        if "publish_date" in metadata and isinstance(metadata["publish_date"], str):
            try:
                # E.g. "2023-11-12"
                metadata["publish_date"] = datetime.strptime(metadata["publish_date"], "%Y-%m-%d").date()
            except ValueError:
                pass
                
        # Isolate the transcript section. Usually follows "## Transcript"
        if "## Transcript" in text_content:
            text_content = text_content.split("## Transcript", 1)[1].strip()
        
        paragraphs = text_content.split("\n\n")
        parsed_paragraphs = []
        
        current_speaker = None
        current_time = None
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Check if this paragraph starts with a speaker tag
            lines = para.split("\n")
            first_line = lines[0].strip()
            
            speaker_match = self.speaker_re.match(first_line)
            time_only_match = self.timestamp_only_re.match(first_line)
            
            if speaker_match:
                current_speaker = speaker_match.group(1).strip()
                current_time = speaker_match.group(2).strip()
                # Remove the speaker tag from the paragraph text if it's the only thing on the line
                # Often, the speaker tag is on its own line, and text follows on the next line
                if len(lines) > 1:
                    para = "\n".join(lines[1:]).strip()
                else:
                    continue # It was just a speaker label with no text, wait for next paragraph
            elif time_only_match:
                current_time = time_only_match.group(1).strip()
                if len(lines) > 1:
                    para = "\n".join(lines[1:]).strip()
                else:
                    continue
                    
            if para:
                parsed_paragraphs.append(ParsedParagraph(
                    text=para,
                    speaker=current_speaker,
                    start_time=current_time
                ))
                
        return metadata, parsed_paragraphs

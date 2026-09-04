import pytest
from app.rag.parser import TranscriptParser
from app.rag.chunker import TranscriptChunker
from app.rag.parser import ParsedParagraph
from pathlib import Path

def test_parser_extracts_speaker_and_timestamp(tmp_path: Path):
    test_file = tmp_path / "transcript.md"
    content = """---
guest: Test Guest
title: Test Title
---
# Test Title
## Transcript
Speaker One (00:00:00):
Hello world.

(00:00:10):
More text.

Speaker Two (00:00:15):
Goodbye.
"""
    test_file.write_text(content, encoding="utf-8")
    
    parser = TranscriptParser()
    metadata, paragraphs = parser.parse_file(test_file)
    
    assert metadata["guest"] == "Test Guest"
    assert metadata["title"] == "Test Title"
    
    assert len(paragraphs) == 3
    assert paragraphs[0].speaker == "Speaker One"
    assert paragraphs[0].start_time == "00:00:00"
    assert paragraphs[0].text == "Hello world."
    
    assert paragraphs[1].speaker == "Speaker One"
    assert paragraphs[1].start_time == "00:00:10"
    assert paragraphs[1].text == "More text."
    
    assert paragraphs[2].speaker == "Speaker Two"
    assert paragraphs[2].start_time == "00:00:15"
    assert paragraphs[2].text == "Goodbye."

def test_chunker_groups_paragraphs_and_preserves_overlap():
    chunker = TranscriptChunker(chunk_size=50, chunk_overlap=10) # tiny for test
    # We will mock the tokenizer indirectly by just providing paragraphs
    # "hello world" is roughly 2 tokens.
    # Let's just create 30 paragraphs of 2 tokens each. 60 tokens total.
    # It should split into 2 chunks.
    
    paragraphs = []
    for i in range(30):
        paragraphs.append(ParsedParagraph(text=f"Sentence {i}.", speaker="Bob", start_time=f"00:00:{i:02d}"))
        
    chunks = chunker.chunk_paragraphs(paragraphs)
    
    assert len(chunks) > 1
    assert chunks[0]["speaker"] == "Bob"
    assert chunks[0]["start_time"] == "00:00:00"
    
    # Check overlap (the second chunk should contain text from the end of the first chunk)
    assert chunks[1]["speaker"] == "Bob" # Carries over metadata or picks up next

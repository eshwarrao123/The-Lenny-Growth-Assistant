import pytest
import httpx
import respx
from app.rag.embeddings import OllamaEmbeddings
from app.rag.parser import TranscriptParser
from pathlib import Path

@pytest.mark.asyncio
async def test_embedding_validation_dimension_check():
    embedder = OllamaEmbeddings()
    
    # Mock Ollama response with correct 768 dimensions
    dummy_vec = [0.1] * 768
    with respx.mock:
        respx.post("http://localhost:11434/api/embed").respond(
            json={"embeddings": [dummy_vec]}
        )
        res = await embedder.embed_batch(["test text"])
        assert len(res) == 1
        assert len(res[0]) == 768

@pytest.mark.asyncio
async def test_embedding_validation_dimension_mismatch_raises():
    embedder = OllamaEmbeddings()
    
    # Mock Ollama response with wrong dimensions (384 instead of 768)
    dummy_vec_wrong = [0.1] * 384
    with respx.mock:
        respx.post("http://localhost:11434/api/embed").respond(
            json={"embeddings": [dummy_vec_wrong]}
        )
        respx.post("http://localhost:11434/api/embeddings").respond(
            json={"embedding": dummy_vec_wrong}
        )
        with pytest.raises(ValueError, match="Embedding dimension mismatch"):
            await embedder.embed_batch(["test text"])

def test_parser_metadata_handling_missing_fields(tmp_path: Path):
    test_file = tmp_path / "transcript.md"
    content = """---
guest: Single Guest
title: Title from Frontmatter
---
# Title from Heading
## Transcript
Speaker (00:01:00):
Some quote here.
"""
    test_file.write_text(content, encoding="utf-8")
    parser = TranscriptParser()
    metadata, paragraphs = parser.parse_file(test_file)
    
    assert metadata["guest"] == "Single Guest"
    assert metadata["title"] == "Title from Frontmatter"
    assert len(paragraphs) == 1
    assert paragraphs[0].speaker == "Speaker"
    assert paragraphs[0].start_time == "00:01:00"

import tiktoken
from typing import List, Dict, Any, Optional
from app.rag.parser import ParsedParagraph
import logging

logger = logging.getLogger(__name__)

class TranscriptChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # We use cl100k_base which is standard and fast, regardless of the target embedding model.
        # It gives very reliable approximate token counts.
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def chunk_paragraphs(self, paragraphs: List[ParsedParagraph]) -> List[Dict[str, Any]]:
        """
        Groups paragraphs sequentially. If a paragraph exceeds chunk_size, it is hard-split.
        Retains speaker and timestamp of the first paragraph in the chunk.
        """
        chunks = []
        current_chunk_text = ""
        current_chunk_tokens = 0
        current_speaker = None
        current_time = None
        chunk_index = 0
        
        # Buffer to keep track of recent paragraphs/texts for overlap
        overlap_buffer = [] 
        
        def commit_chunk():
            nonlocal current_chunk_text, current_chunk_tokens, current_speaker, current_time, chunk_index, overlap_buffer
            if not current_chunk_text.strip():
                return
                
            chunks.append({
                "chunk_index": chunk_index,
                "text": current_chunk_text.strip(),
                "token_count": current_chunk_tokens,
                "speaker": current_speaker,
                "start_time": current_time
            })
            chunk_index += 1
            
            # Prepare next chunk with overlap
            # We take items from overlap buffer until we hit ~100 tokens
            overlap_text = ""
            overlap_tokens = 0
            # iterate backwards to grab most recent text for overlap
            for text_snippet in reversed(overlap_buffer):
                toks = self.count_tokens(text_snippet)
                if overlap_tokens + toks <= self.chunk_overlap:
                    overlap_text = text_snippet + "\n\n" + overlap_text
                    overlap_tokens += toks
                else:
                    break
                    
            current_chunk_text = overlap_text
            current_chunk_tokens = overlap_tokens
            overlap_buffer = [overlap_text.strip()] if overlap_text.strip() else []
            # We don't reset speaker here; the next paragraph will define the new speaker if it changes, 
            # or we will inherit the last one if we have to. For simplicity, we'll let the next 
            # added paragraph set the speaker/time if it's currently None, or keep the old one.
            # But usually it's better to clear it and let the overlap or next paragraph set it.
            # However, if we carry over text, we ideally want to keep the metadata of the last active speaker.
            
        for para in paragraphs:
            para_tokens = self.count_tokens(para.text)
            
            if current_chunk_tokens == 0 or current_speaker is None:
                current_speaker = para.speaker or current_speaker
                current_time = para.start_time or current_time
                
            # If a single paragraph is larger than chunk size, we must hard split it
            if para_tokens > self.chunk_size:
                # First, commit whatever we currently have
                if current_chunk_tokens > 0:
                    commit_chunk()
                
                # Update metadata for the big paragraph
                current_speaker = para.speaker or current_speaker
                current_time = para.start_time or current_time
                
                # Split the big paragraph by sentences or naive chunks
                # We'll use a naive split by keeping adding words
                words = para.text.split(" ")
                temp_text = ""
                temp_toks = 0
                
                for word in words:
                    wt = self.count_tokens(word + " ")
                    if temp_toks + wt > self.chunk_size:
                        current_chunk_text = temp_text
                        current_chunk_tokens = temp_toks
                        commit_chunk()
                        temp_text = word + " "
                        temp_toks = wt
                    else:
                        temp_text += word + " "
                        temp_toks += wt
                        
                # Whatever is left goes into the current buffer
                if temp_text.strip():
                    current_chunk_text = temp_text
                    current_chunk_tokens = temp_toks
                    overlap_buffer.append(temp_text.strip())
                continue
                
            # Normal paragraph flow
            if current_chunk_tokens + para_tokens > self.chunk_size:
                commit_chunk()
                current_speaker = para.speaker or current_speaker
                current_time = para.start_time or current_time
                
            current_chunk_text += para.text + "\n\n"
            current_chunk_tokens += para_tokens
            overlap_buffer.append(para.text)
            
        if current_chunk_tokens > 0:
            commit_chunk()
            
        return chunks

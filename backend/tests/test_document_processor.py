import pytest
from app.services.document_processor import DocumentProcessor

@pytest.fixture
def processor():
    return DocumentProcessor()

def test_chunk_text_overlap(processor):
    text = "A" * 600 + "B" * 600 + "C" * 600  # 1800 chars
    # A: 0-599, B: 600-1199, C: 1200-1799
    chunks = processor._chunk_text(text, {})

    # 4 chunks with step=450 (CHUNK_SIZE=500, CHUNK_OVERLAP=50):
    # Chunk 0: 0-500 → 500 A's
    # Chunk 1: 450-950 → 150 A's + 350 B's
    # Chunk 2: 900-1400 → 300 B's + 200 C's
    # Chunk 3: 1350-1800 → 450 C's
    assert len(chunks) == 4
    assert chunks[0][0] == "A" * 500
    assert chunks[0][1]["start_char"] == 0
    assert chunks[1][0] == "A" * 150 + "B" * 350
    assert chunks[1][1]["start_char"] == 450
    assert chunks[2][0] == "B" * 300 + "C" * 200
    assert chunks[2][1]["start_char"] == 900
    assert chunks[3][0] == "C" * 450
    assert chunks[3][1]["start_char"] == 1350

def test_chunk_text_removes_whitespace(processor):
    text = "Hello    World\n\n\nTest"
    chunks = processor._chunk_text(text, {})
    assert "\n" not in chunks[0][0]
    assert "  " not in chunks[0][0]

import requests
import os
import json
import pandas as pd
import urllib3

SERVER_URL = os.environ.get("SERVER_URL", "https://smart.ucsd.edu")

# Disable SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a session that skips SSL verification (production uses self-signed cert)
session = requests.Session()
session.verify = False

# Swinholide A example data from the HTML interface
SWINHOLIDE_A_PEAKS = [
    {"1H": 5.79, "13C": 113.2},
    {"1H": 7.58, "13C": 153.3},
    {"1H": 1.88, "13C": 12.3},
    {"1H": 6.08, "13C": 142.2},
    {"1H": 2.46, "13C": 37.4},
    {"1H": 2.18, "13C": 37.4},
    {"1H": 4.14, "13C": 66.6},
    {"1H": 1.58, "13C": 40.8},
    {"1H": 1.73, "13C": 40.8},
    {"1H": 4.51, "13C": 65.7},
    {"1H": 5.69, "13C": 129.8},
    {"1H": 5.78, "13C": 123.2},
    {"1H": 1.82, "13C": 29.9},
    {"1H": 2.27, "13C": 29.9},
    {"1H": 3.86, "13C": 65.8},
    {"1H": 1.46, "13C": 33.8},
    {"1H": 2.14, "13C": 33.8},
    {"1H": 4.01, "13C": 75.1},
    {"1H": 3.35, "13C": 57.4},
    {"1H": 1.68, "13C": 41.0},
    {"1H": 0.81, "13C": 9.4},
    {"1H": 3.83, "13C": 73.8},
    {"1H": 1.62, "13C": 38.4},
    {"1H": 3.98, "13C": 71.3},
    {"1H": 1.75, "13C": 41.3},
    {"1H": 0.97, "13C": 9.2},
    {"1H": 5.36, "13C": 74.3},
    {"1H": 1.95, "13C": 37.6},
    {"1H": 0.84, "13C": 9.1},
    {"1H": 3.12, "13C": 76.0},
    {"1H": 1.65, "13C": 33.2},
    {"1H": 0.99, "13C": 17.7},
    {"1H": 1.27, "13C": 23.9},
    {"1H": 1.38, "13C": 23.9},
    {"1H": 1.30, "13C": 29.3},
    {"1H": 1.90, "13C": 29.3},
    {"1H": 4.02, "13C": 71.4},
    {"1H": 1.60, "13C": 34.8},
    {"1H": 1.82, "13C": 34.8},
    {"1H": 3.53, "13C": 73.2},
    {"1H": 3.33, "13C": 55.2},
    {"1H": 1.18, "13C": 38.8},
    {"1H": 1.96, "13C": 38.8},
    {"1H": 3.69, "13C": 64.5},
    {"1H": 1.20, "13C": 21.7},
]

SWINHOLIDE_A_CSV = "1H,13C\n" + "\n".join(
    f"{p['1H']},{p['13C']}" for p in SWINHOLIDE_A_PEAKS
)


def test_heartbeat():
    """Test that the server is alive."""
    r = session.get(f"{SERVER_URL}/heartbeat")
    r.raise_for_status()
    assert r.status_code == 200


def test_classic_page():
    """Test that the classic page loads."""
    r = session.get(f"{SERVER_URL}/classic")
    r.raise_for_status()
    assert "SMART" in r.text


def test_api_embed():
    """Test the /api/classic/embed endpoint with Swinholide A example data."""
    r = session.post(
        f"{SERVER_URL}/api/classic/embed",
        data={"peaks": json.dumps(SWINHOLIDE_A_PEAKS)},
    )
    r.raise_for_status()

    result = r.json()

    # Should return an embedding with 180 dimensions
    assert "embedding" in result, f"Response missing 'embedding' key: {list(result.keys())}"
    assert len(result["embedding"]) == 180, f"Expected 180-dim embedding, got {len(result['embedding'])}"


def test_api_search_tsv():
    """Test the /api/classic/search endpoint returns TSV results."""
    r = session.post(
        f"{SERVER_URL}/api/classic/search",
        data={"peaks": json.dumps(SWINHOLIDE_A_PEAKS)},
    )
    r.raise_for_status()

    # Should return a TSV table
    lines = r.text.strip().split("\n")
    assert len(lines) > 1, "Expected result table with header + rows"

    # Parse as TSV and check columns
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    assert len(df) > 0, "Expected at least one result row"
    print(f"  Search returned {len(df)} results")
    print(f"  Columns: {list(df.columns)}")


def test_api_search_json():
    """Test the /api/classic/search endpoint with json=json returns JSON results."""
    r = session.post(
        f"{SERVER_URL}/api/classic/search",
        data={"peaks": json.dumps(SWINHOLIDE_A_PEAKS), "json": "json"},
    )
    r.raise_for_status()

    results = r.json()
    assert isinstance(results, list), f"Expected list of results, got {type(results)}"
    assert len(results) > 0, "Expected at least one search result"

    # Check that results have expected fields
    first = results[0]
    print(f"  JSON search returned {len(results)} results")
    print(f"  Result keys: {list(first.keys())}")

    # Verify Swinholide A appears in top results (it's the example compound)
    names = [r.get("name", r.get("Name", "")) for r in results[:10]]
    print(f"  Top 10 names: {names}")


def test_analyze_entry():
    """Test the /analyzeentryclassic endpoint with CSV peak data."""
    r = session.post(
        f"{SERVER_URL}/analyzeentryclassic",
        data={"peaks": SWINHOLIDE_A_CSV},
    )
    r.raise_for_status()

    result = r.json()
    assert "task" in result, f"Response missing 'task' key: {result}"
    task_id = result["task"]
    print(f"  Task ID: {task_id}")

    # Verify embedding endpoint works with the task
    r = session.get(f"{SERVER_URL}/embedding_json_classic/{task_id}")
    r.raise_for_status()
    embed_config = r.json()
    assert "embeddings" in embed_config
    assert len(embed_config["embeddings"]) > 0

    # Check embedding dimensions
    tensor_shape = embed_config["embeddings"][0]["tensorShape"]
    assert tensor_shape[0] > 1, f"Expected more than 1 row, got {tensor_shape[0]}"
    assert tensor_shape[1] == 180, f"Expected 180 columns, got {tensor_shape[1]}"
    print(f"  Embedding shape: {tensor_shape}")

    # Verify metadata endpoint
    r = session.get(f"{SERVER_URL}/embedding_metadata_classic/{task_id}")
    r.raise_for_status()
    assert len(r.text) > 0

    # Verify embedding data endpoint
    r = session.get(f"{SERVER_URL}/embedding_data_classic/{task_id}")
    r.raise_for_status()
    assert len(r.text) > 0

    # Verify results table endpoint
    r = session.get(f"{SERVER_URL}/resultclassictable?task={task_id}")
    r.raise_for_status()
    df = pd.read_csv(pd.io.common.StringIO(r.text))
    assert len(df) > 0, "Expected results in table"
    print(f"  Results table: {len(df)} rows")


def test_analyze_upload():
    """Test the /analyzeuploadclassic endpoint with file upload."""
    r = session.post(
        f"{SERVER_URL}/analyzeuploadclassic",
        files={"file": ("swinholide_a.csv", SWINHOLIDE_A_CSV, "text/csv")},
    )
    r.raise_for_status()

    result = r.json()
    assert "task" in result, f"Response missing 'task' key: {result}"
    task_id = result["task"]
    print(f"  Task ID: {task_id}")

    # Verify result page loads
    r = session.get(f"{SERVER_URL}/resultclassic?task={task_id}")
    r.raise_for_status()
    assert "SMART" in r.text

    # Verify NMR image endpoint
    r = session.get(f"{SERVER_URL}/result_nmr?task={task_id}")
    r.raise_for_status()
    assert r.headers.get("Content-Type", "").startswith("image/"), \
        f"Expected image content type, got {r.headers.get('Content-Type')}"
    assert len(r.content) > 100, "Expected non-trivial image data"
    print(f"  NMR image size: {len(r.content)} bytes")


def test_global_embeddings():
    """Test the global embedding endpoints."""
    # Config
    r = session.get(f"{SERVER_URL}/embedding_json_classic_global")
    r.raise_for_status()
    config = r.json()
    assert "embeddings" in config
    tensor_shape = config["embeddings"][0]["tensorShape"]
    assert tensor_shape[0] > 100, f"Expected large database, got {tensor_shape[0]} entries"
    assert tensor_shape[1] == 180
    print(f"  Global database size: {tensor_shape[0]} compounds")

    # Data
    r = session.get(f"{SERVER_URL}/embedding_data_classic_global")
    r.raise_for_status()
    assert len(r.text) > 0

    # Metadata
    r = session.get(f"{SERVER_URL}/embedding_metadata_classic_global")
    r.raise_for_status()
    assert len(r.text) > 0

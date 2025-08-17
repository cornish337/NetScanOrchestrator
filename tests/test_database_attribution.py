import os
import tempfile
import sqlite3
import json
import pytest
import time

def test_entity_linkage(temp_db_path, cli_runner):
    """
    Tests that database records are correctly linked after multiple scans.
    - A Target should link to multiple Jobs.
    - Each Job should link to a unique ScanRun and a Result.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("scanme.nmap.org\n")
        input_file = f.name

    try:
        cli_runner("ingest", input_file, db_path=temp_db_path)

        output1 = cli_runner("plan", "--options", "-F", db_path=temp_db_path)
        run_id_1 = int(output1.split()[-1])
        cli_runner("split", run_id_1, "--chunk-size", "1", db_path=temp_db_path)
        cli_runner("run", run_id_1, db_path=temp_db_path)

        output2 = cli_runner("plan", "--options", "-sV --top-ports 10", db_path=temp_db_path)
        run_id_2 = int(output2.split()[-1])
        cli_runner("split", run_id_2, "--chunk-size", "1", db_path=temp_db_path)
        cli_runner("run", run_id_2, db_path=temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, address FROM targets")
        targets = cur.fetchall()
        assert len(targets) == 1
        target_id = targets[0][0]
        assert targets[0][1] in ("scanme.nmap.org", "45.33.32.156")

        cur.execute("SELECT id, options, status, started_at, completed_at FROM scan_runs ORDER BY id")
        runs = cur.fetchall()
        assert len(runs) == 2
        assert runs[0][0] == run_id_1
        assert runs[0][1] == "-F"
        assert runs[0][2] == "COMPLETED"
        assert runs[0][3] is not None and runs[0][4] is not None
        assert runs[1][0] == run_id_2
        assert runs[1][1] == "-sV --top-ports 10"
        assert runs[1][2] == "COMPLETED"
        assert runs[1][3] is not None and runs[1][4] is not None

        cur.execute("SELECT id, scan_run_id, target_id FROM jobs ORDER BY id")
        jobs = cur.fetchall()
        assert len(jobs) == 2
        job_id_1, job_id_2 = jobs[0][0], jobs[1][0]
        assert jobs[0][1] == run_id_1
        assert jobs[0][2] == target_id
        assert jobs[1][1] == run_id_2
        assert jobs[1][2] == target_id

        cur.execute("SELECT job_id, summary_json FROM results ORDER BY job_id")
        results = cur.fetchall()
        assert len(results) == 2
        assert results[0][0] == job_id_1
        assert results[1][0] == job_id_2
        assert results[0][1] is not None and len(results[0][1]) > 0
        assert results[1][1] is not None and len(results[1][1]) > 0

        conn.close()

    finally:
        os.unlink(input_file)

def test_ingest_is_idempotent(temp_db_path, cli_runner):
    """Tests that ingesting the same target twice does not create duplicates."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("localhost\n")
        input_file = f.name

    try:
        output1 = cli_runner("ingest", input_file, db_path=temp_db_path)
        assert "Ingested 1 new targets" in output1
        assert "Skipped 0 duplicates" in output1

        output2 = cli_runner("ingest", input_file, db_path=temp_db_path)
        assert "Ingested 0 new targets" in output2
        assert "Skipped 1 duplicates" in output2

        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM targets")
        assert cur.fetchone()[0] == 1
        conn.close()
    finally:
        os.unlink(input_file)

def test_single_run_aggregation(client_with_db, temp_db_path, cli_runner):
    """
    Tests that the API can correctly aggregate results for a single scan run
    with multiple targets.
    """
    response = client_with_db.post(
        "/api/scans",
        json={"targets": ["scanme.nmap.org", "example.com"], "nmap_options": "-F"},
    )
    assert response.status_code == 202
    scan_id = response.json()["scan_id"]

    for _ in range(60):
        response = client_with_db.get(f"/api/scans/{scan_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        if data["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(1)
    else:
        pytest.fail("Scan did not complete in 60 seconds")

    assert data["status"] == "COMPLETED"
    results = data["results"]["hosts"]

    assert len(results) == 2
    assert "scanme.nmap.org" in results
    assert "example.com" in results

    assert results["scanme.nmap.org"]["status"] == "up"
    assert len(results["scanme.nmap.org"]["ports"]) > 0

    assert results["example.com"]["status"] in ("up", "down")
    if results["example.com"]["status"] == "up":
        assert len(results["example.com"]["ports"]) > 0

    cli_output = cli_runner("status", db_path=temp_db_path)
    expected_summary_line = f"{scan_id:<5} {2:<6} {2:<9} {0:<6}"
    assert expected_summary_line in cli_output

def test_multi_scan_aggregation(temp_db_path, cli_runner):
    """
    Tests that data from multiple scans on the same target is stored correctly
    and can be aggregated.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("scanme.nmap.org\n")
        input_file = f.name

    try:
        cli_runner("ingest", input_file, db_path=temp_db_path)

        output1 = cli_runner("plan", "--options", "-F", db_path=temp_db_path)
        run_id_1 = int(output1.split()[-1])
        cli_runner("split", run_id_1, "--chunk-size", "1", db_path=temp_db_path)
        cli_runner("run", run_id_1, db_path=temp_db_path)

        output2 = cli_runner("plan", "--options", "-sV --top-ports 10", db_path=temp_db_path)
        run_id_2 = int(output2.split()[-1])
        cli_runner("split", run_id_2, "--chunk-size", "1", db_path=temp_db_path)
        cli_runner("run", run_id_2, db_path=temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute("SELECT r.summary_json FROM results r JOIN jobs j ON r.job_id = j.id JOIN targets t ON j.target_id = t.id WHERE t.address = 'scanme.nmap.org'")
        results = cur.fetchall()
        conn.close()

        assert len(results) == 2

        all_open_ports = set()
        for res_tuple in results:
            summary_json = res_tuple[0]
            if summary_json:
                summary = json.loads(summary_json)
                host_data = next(iter(summary.values()), None)
                if host_data and isinstance(host_data, dict):
                    ports = host_data.get("tcp", {}).keys()
                    all_open_ports.update(int(p) for p in ports)

        assert 22 in all_open_ports
        assert 80 in all_open_ports

    finally:
        os.unlink(input_file)

def test_resplit_workflow(temp_db_path, cli_runner):
    """Tests the 'resplit' CLI command and parent-child batch relationships."""
    targets = [f"192.168.1.{i}" for i in range(5)]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("\n".join(targets))
        input_file = f.name

    try:
        cli_runner("ingest", input_file, db_path=temp_db_path)
        output = cli_runner("plan", db_path=temp_db_path)
        run_id = int(output.split()[-1])
        cli_runner("split", run_id, "--chunk-size", "5", db_path=temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM batches")
        parent_batch_id = cur.fetchone()[0]
        conn.close()

        cli_runner("resplit", parent_batch_id, "--chunk-size", "2", db_path=temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, parent_batch_id, strategy FROM batches WHERE parent_batch_id = ?", (parent_batch_id,))
        child_batches = cur.fetchall()

        assert len(child_batches) == 3

        for batch in child_batches:
            assert batch[1] == parent_batch_id
            assert batch[2] == "resplit"

        cur.execute("SELECT COUNT(*) FROM batch_target_association WHERE batch_id IN (SELECT id FROM batches WHERE parent_batch_id = ?)", (parent_batch_id,))
        child_target_count = cur.fetchone()[0]
        assert child_target_count == 5
        conn.close()

    finally:
        os.unlink(input_file)

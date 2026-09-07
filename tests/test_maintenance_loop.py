import shutil
from compart.maintenance import detect_drift, run_maintenance_cycle, get_migration_history


def test_detect_drift_in_fixture():
    fixture_dir = "trials/fixtures/taxonomy_stripe"
    detected = detect_drift(fixture_dir)
    assert len(detected) >= 1
    stripe_dep = next((d for d in detected if d["provider"] == "stripe"), None)
    assert stripe_dep is not None
    assert stripe_dep["declared_version"] == "^11.18.0"


def test_run_maintenance_cycle_taxonomy(tmp_path):
    fixture_dir = "trials/fixtures/taxonomy_stripe"
    target_dir = str(tmp_path / "taxonomy_stripe")
    shutil.copytree(fixture_dir, target_dir)

    report = run_maintenance_cycle(
        repo_dir=target_dir,
        provider_name="stripe",
        from_version="11.18.0",
        to_version="22.0.0",
        create_pr=False,
    )

    assert report.provider_name == "stripe"
    assert report.from_version == "11.18.0"
    assert report.to_version == "22.0.0"
    assert report.blast_radius_verified is True
    assert report.unintended_files_modified == 0
    assert "Autonomous Maintenance" in report.trust_pr_body
    assert "Blast Radius Containment" in report.trust_pr_body

    history = get_migration_history(target_dir)
    assert len(history) > 0
    latest = history[-1]
    assert latest["provider_name"].lower() == "stripe"
    assert latest["blast_radius_zero"] is True

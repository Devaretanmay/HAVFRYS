from compart.maintenance_agents import (
    ChangeAnalyzer,
    ImpactAnalyst,
    PatchPlanner,
    PatchVerifier,
    AutonomousMaintenancePipeline,
)


def test_change_analyzer_stripe():
    analyzer = ChangeAnalyzer()
    res = analyzer.analyze("stripe")
    assert res.provider == "stripe"
    assert res.from_version is not None
    assert res.to_version is not None


def test_impact_analyst_dummy(tmp_path):
    analyst = ImpactAnalyst()
    res = analyst.analyze_impact(str(tmp_path), "stripe")
    assert res.provider == "stripe"
    assert isinstance(res.affected_files, list)


def test_patch_planner_dummy(tmp_path):
    analyzer = ChangeAnalyzer()
    change_res = analyzer.analyze("stripe")
    planner = PatchPlanner()
    plan_res = planner.plan(str(tmp_path), change_res)
    assert plan_res.provider == "stripe"
    assert isinstance(plan_res.targets, list)


def test_patch_verifier_success(tmp_path):
    verifier = PatchVerifier()
    test_script = tmp_path / "test.sh"
    test_script.write_text("#!/bin/sh\necho 'all tests pass'\nexit 0\n")
    test_script.chmod(0o755)

    res = verifier.verify(str(tmp_path), test_cmd=f"sh {test_script}")
    assert res.success
    assert res.test_exit_code == 0
    assert "all tests pass" in res.compressed_execution_log


def test_patch_verifier_failure(tmp_path):
    verifier = PatchVerifier()
    test_script = tmp_path / "fail.sh"
    test_script.write_text("#!/bin/sh\necho 'error stack trace'\nexit 1\n")
    test_script.chmod(0o755)

    res = verifier.verify(str(tmp_path), test_cmd=f"sh {test_script}")
    assert not res.success
    assert res.test_exit_code == 1


def test_autonomous_maintenance_pipeline_mock(tmp_path):
    pipeline = AutonomousMaintenancePipeline()
    res = pipeline.run(str(tmp_path), "stripe")
    assert "success" in res
    assert res["provider"] == "stripe"

from compart.maintenance_agents import ImpactAnalyst


def test_impact_analyst_dummy(tmp_path):
    analyst = ImpactAnalyst()
    res = analyst.analyze_impact(str(tmp_path), "stripe")
    assert res.provider == "stripe"
    assert isinstance(res.affected_files, list)

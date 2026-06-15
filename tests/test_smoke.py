from repo_roast.core import roast


def test_heuristic(tmp_path):
    (tmp_path / "README.md").write_text("hi")
    res = roast(str(tmp_path), use_llm=False)
    assert 0 <= res["score"] <= 100 and res["roast"]

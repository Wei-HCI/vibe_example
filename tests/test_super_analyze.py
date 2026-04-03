from pathlib import Path

from rcode.super_analyze import build_method_recommendations, build_scan_report


ROOT = Path(__file__).resolve().parents[1]


def test_scan_detects_ipq() -> None:
    report = build_scan_report(ROOT / "text_dataset" / "ipq.csv")

    assert report["questionnaire"]["name"] == "IPQ"
    assert report["questionnaire"]["confidence"] in {"HIGH", "MEDIUM"}
    assert report["subject_id_column"] == "Participant.ID"
    assert report["condition_column"] == "Which.Condition."
    assert report["design"]["type"] == "within-subjects"
    assert set(report["dependent_variables"]) >= {"SP", "INV", "REAL"}


def test_scan_detects_ssq() -> None:
    report = build_scan_report(ROOT / "text_dataset" / "ssq.csv")

    assert report["questionnaire"]["name"] == "SSQ"
    assert report["subject_id_column"] == "Participant.ID"
    assert report["condition_column"] == "Which.Condition."


def test_scan_flags_wide_nasa_layout() -> None:
    report = build_scan_report(ROOT / "text_dataset" / "Nasa_tlx.xlsx")

    assert report["questionnaire"]["name"] == "NASA-TLX"
    assert report["design"]["wide_layout"] is True
    assert any("wide" in item.lower() or "multi-block" in item.lower() for item in report["stop_conditions"])


def test_recommend_ipq_methods() -> None:
    result = build_method_recommendations(ROOT / "text_dataset" / "ipq.csv")
    methods = {item["dv"]: item["recommended_method"] for item in result["recommendations"]}

    assert methods["IPQ_SP"] == "repeated-measures ANOVA"
    assert methods["IPQ_INV"] == "repeated-measures ANOVA"
    assert methods["IPQ_REAL"] == "Friedman test"

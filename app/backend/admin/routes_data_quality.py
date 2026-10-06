"""Admin Data Quality & Profiling Routes (Module 14.3)"""
from flask import jsonify, render_template, request
from .utils import admin_required
from app.backend.admin.data_quality_service import (
    get_data_profiling,
    scan_data_quality_issues,
    autofill_vocab_data,
    batch_autofill_substandard_vocab
)
from app.backend.admin import bp


@bp.route("/data-quality", methods=["GET"])
@admin_required
def data_quality_dashboard():
    """Main Data Quality & Profiling Dashboard."""
    profiling = get_data_profiling()
    scan_results = scan_data_quality_issues()
    return render_template(
        "admin/data_quality.html",
        profiling=profiling,
        summary=scan_results["summary"],
        vocab_issues=scan_results["vocab_issues"],
        question_issues=scan_results["question_issues"],
        lesson_issues=scan_results["lesson_issues"],
        scanned_at=scan_results["scanned_at"],
    )


@bp.route("/data-quality/report", methods=["GET"])
@admin_required
def data_quality_report():
    """Detailed Data Quality Report view with filter and JSON export."""
    fmt = request.args.get("format", "html")
    scan_results = scan_data_quality_issues()
    profiling = get_data_profiling()

    if fmt == "json":
        return jsonify({
            "profiling": profiling,
            "scan_results": scan_results
        })

    return render_template(
        "admin/data_quality.html",
        profiling=profiling,
        summary=scan_results["summary"],
        vocab_issues=scan_results["vocab_issues"],
        question_issues=scan_results["question_issues"],
        lesson_issues=scan_results["lesson_issues"],
        scanned_at=scan_results["scanned_at"],
        is_report_view=True
    )


@bp.route("/data-quality/api/profile", methods=["GET"])
@admin_required
def api_data_profiling():
    """JSON API returning current profiling stats."""
    return jsonify(get_data_profiling())


@bp.route("/data-quality/api/scan", methods=["POST"])
@admin_required
def api_data_quality_scan():
    """Triggers an on-demand database scan."""
    results = scan_data_quality_issues()
    return jsonify({"ok": True, "results": results})


@bp.route("/data-quality/api/autofill/<int:vocab_id>", methods=["POST"])
@admin_required
def api_autofill_vocab(vocab_id):
    """Auto-fills missing IPA and definition data for a specific vocabulary record."""
    res = autofill_vocab_data(vocab_id)
    if res.get("success"):
        return jsonify({"ok": True, "result": res})
    return jsonify({"ok": False, "error": res.get("error", "Lỗi không xác định")}), 400


@bp.route("/data-quality/api/batch-autofill", methods=["POST"])
@admin_required
def api_batch_autofill_vocab():
    """Batches quality improvement across substandard vocabularies."""
    limit = request.json.get("limit", 30) if request.is_json else 30
    res = batch_autofill_substandard_vocab(limit=limit)
    return jsonify({"ok": True, "result": res})

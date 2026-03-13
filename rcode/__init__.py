"""
rcode - Enhanced Python Functions for Statistical Analysis and APA-Compliant Reporting.

A Python port of the R package rCode by Mark Colley.
"""

__version__ = "0.1.0"

from rcode.setup import rcode_setup as setup
from rcode.utils import (
    na_zero,
    normalize,
    path_prep,
    n_fun,
    having_ip,
    not_in,
)
from rcode.assumptions import (
    check_normality_by_group,
    check_assumptions_for_anova,
)
from rcode.reporting import (
    report_npav,
    report_npav_chi,
    report_art,
    report_npar_ld,
    report_mean_and_sd,
    report_dunn_test,
    report_dunn_test_table,
    r_from_wilcox,
    report_pairwise_paper_style,
    r_from_npav,
    latexify_report,
)
from rcode.visualization import (
    gg_withinstats_with_normality_check,
    gg_betweenstats_with_normality_check,
    generate_effect_plot,
    generate_mobo_plot,
)
from rcode.data_processing import (
    replace_values,
    add_pareto_column,
    remove_outliers_rei,
)
from rcode.questionnaire_processing import (
    process_ipq,
    process_ssq,
    process_sus,
)

#!/bin/bash
# Run all ab q7 cases locally via q8020-sweeper.
set -euo pipefail

TOML_DIR=./q8020-mps-burgers/input/ab-q7

# Cases 1-3 already completed 2026-06-14 (nu015/nu020/nu030) — skip on rerun.
# q8020-sweeper $TOML_DIR/burgers_ab_mutual_q7_nu015.toml
# q8020-sweeper $TOML_DIR/burgers_ab_mutual_q7_nu020.toml
# q8020-sweeper $TOML_DIR/burgers_ab_mutual_q7_nu030.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q7_nu050.toml
q8020-sweeper $TOML_DIR/burgers_ab_shock_q7.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q7_ch_smooth.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q7_ch_stress.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q7_qlbm_margin.toml

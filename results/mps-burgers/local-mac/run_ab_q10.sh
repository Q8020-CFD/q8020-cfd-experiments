#!/bin/bash
# Run all ab q10 cases locally via q8020-sweeper.
set -euo pipefail

TOML_DIR=./q8020-mps-burgers/input/ab-q10

q8020-sweeper $TOML_DIR/burgers_ab_mutual_q10_nu015.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q10_nu020.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q10_nu030.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q10_nu050.toml
q8020-sweeper $TOML_DIR/burgers_ab_shock_q10.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q10_ch_smooth.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q10_ch_stress.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q10_qlbm_margin.toml

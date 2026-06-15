#!/bin/bash
# Run all ab q6 cases locally via q8020-sweeper.
set -euo pipefail

TOML_DIR=./q8020-mps-burgers/input/ab-q6

q8020-sweeper $TOML_DIR/burgers_ab_mutual_q6_nu015.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q6_nu020.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q6_nu030.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q6_nu050.toml
q8020-sweeper $TOML_DIR/burgers_ab_shock_q6.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q6_ch_smooth.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q6_ch_stress.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q6_qlbm_margin.toml

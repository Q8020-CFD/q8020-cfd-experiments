#!/bin/bash
# Run all ab q4 cases locally via q8020-sweeper.
set -euo pipefail

TOML_DIR=./q8020-mps-burgers/input/q4

q8020-sweeper $TOML_DIR/burgers_ab_mutual_q4_nu015.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q4_nu020.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q4_nu030.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q4_nu050.toml
q8020-sweeper $TOML_DIR/burgers_ab_shock_q4.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q4_ch_smooth.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q4_ch_stress.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q4_qlbm_margin.toml

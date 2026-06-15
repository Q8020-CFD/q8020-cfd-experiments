#!/bin/bash
# Run all ab q8 cases locally via q8020-sweeper.
set -euo pipefail

TOML_DIR=./q8020-mps-burgers/input/ab-q8

q8020-sweeper $TOML_DIR/burgers_ab_mutual_q8_nu015.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q8_nu020.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q8_nu030.toml
q8020-sweeper $TOML_DIR/burgers_ab_mutual_q8_nu050.toml
q8020-sweeper $TOML_DIR/burgers_ab_shock_q8.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q8_ch_smooth.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q8_ch_stress.toml
q8020-sweeper $TOML_DIR/burgers_ab_show_q8_qlbm_margin.toml

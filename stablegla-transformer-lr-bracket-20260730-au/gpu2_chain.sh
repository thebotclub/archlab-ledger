#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-transformer-lr-bracket-20260730-au/s1_lr1em6/pid
cd /home/hani/archlab-runs/stablegla-transformer-lr-bracket-20260730-au/s1_lr1em6 && CUDA_VISIBLE_DEVICES=2 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1

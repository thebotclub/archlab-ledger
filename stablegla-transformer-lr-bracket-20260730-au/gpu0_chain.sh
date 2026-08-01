#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-transformer-lr-bracket-20260730-au/s1_lr3em5/pid
cd /home/hani/archlab-runs/stablegla-transformer-lr-bracket-20260730-au/s1_lr3em5 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1

#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g2_w96/pid
echo $$ > /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g3_w128/pid
cd /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g2_w96 && CUDA_VISIBLE_DEVICES=2 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g3_w128 && CUDA_VISIBLE_DEVICES=2 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1

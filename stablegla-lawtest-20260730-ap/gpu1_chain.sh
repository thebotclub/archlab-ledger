#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g1_w160/pid
echo $$ > /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g3_w96/pid
cd /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g1_w160 && CUDA_VISIBLE_DEVICES=1 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g3_w96 && CUDA_VISIBLE_DEVICES=1 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1

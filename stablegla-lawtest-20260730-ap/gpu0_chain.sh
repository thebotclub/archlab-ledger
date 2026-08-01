#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g1_w96/pid
echo $$ > /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g3_w64/pid
cd /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g1_w96 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-lawtest-20260730-ap/g3_w64 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1

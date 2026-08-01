#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/core_gpu0/pid
echo $$ > /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/lr6e15_1em3/pid
echo $$ > /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/lr1p2e16_1em3/pid
cd /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/core_gpu0 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/lr6e15_1em3 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/lr1p2e16_1em3 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1

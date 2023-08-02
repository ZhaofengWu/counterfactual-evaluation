#!/usr/bin/bash

# important for reproducibility as we use some Set structures
export PYTHONHASHSEED=0

export PYTHONPATH=./

SEED=42
ROUNDS=100
LOAD_DATA="True"

for COT in False True; do
    EXP_NAME="set/logs/cot_${COT}/"
    mkdir -p ${EXP_NAME}
    python set/set_game.py --model"=gpt-4-0314" --rounds=${ROUNDS} --seed=${SEED} --cot=${COT} --load_data=${LOAD_DATA} > ${EXP_NAME}/gpt4_${ROUNDS}.log 2> ${EXP_NAME}/gpt4_${ROUNDS}.err
    python set/set_game.py --model="gpt-3.5-turbo-0301" --rounds=${ROUNDS} --seed=${SEED} --cot=${COT} --load_data=${LOAD_DATA} > ${EXP_NAME}/gpt3.5_${ROUNDS}.log 2> ${EXP_NAME}/gpt3.5_${ROUNDS}.err
    python set/set_game.py --model="models/text-bison-001" --rounds=${ROUNDS} --seed=${SEED} --cot=${COT} --load_data=${LOAD_DATA}> ${EXP_NAME}/palm_text_${ROUNDS}.log 2> ${EXP_NAME}/palm_text_${ROUNDS}.err
    python set/set_game.py --model="claude-v1.3" --rounds=${ROUNDS} --seed=${SEED}  --cot=${COT} --load_data=${LOAD_DATA} > ${EXP_NAME}/claudev1.3_${ROUNDS}.log 2> ${EXP_NAME}/claudev1.3_${ROUNDS}.err
done

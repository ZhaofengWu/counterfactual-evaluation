export PYTHONPATH=.
EXP_NAME=music/chords/output
MODELS='gpt-4-0314 gpt-3.5-turbo-0301 claude-v1.3 models/text-bison-001'

INSTRUMENT=guitar
TUNINGS='EADGBE DADGBE FADGBE EBDGBE ECDGBE ECFGBE'
for TUNING in $TUNINGS
do
	for MODEL in $MODELS
	do
		############# CCC ############

		# with chain of thought (let's think step by step)
		python music/chords/query.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING \
			--chain_of_thought \
			--is_control

		python music/chords/eval.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING \
			--chain_of_thought \
			--is_control

		# no COT
		python music/chords/query.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING \
			--is_control

		python music/chords/eval.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING \
			--is_control


		############# TASK ############

		# with chain of thought (let's think step by step)
		python music/chords/query.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING \
			--chain_of_thought

		python music/chords/eval.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING \
			--chain_of_thought

		# no COT
		python music/chords/query.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING

		python music/chords/eval.py \
			--model $MODEL \
			--exp_dir $EXP_NAME \
			--instrument $INSTRUMENT \
			--tunings $TUNING
	done
done

export PYTHONPATH=.
MODELS='gpt-4-0314 gpt-3.5-turbo-0301 models/text-bison-001 claude-v1.3'
EXP_NAME=music/melodies/output

for MODEL in $MODELS
do
	############# CCC ############
	# no COT
	python music/melodies/query.py \
		--model $MODEL \
		--exp_dir $EXP_NAME \
		--is_control

	python music/melodies/eval.py \
		--model $MODEL \
		--exp_dir $EXP_NAME \
		--is_control

	# with chain of thought (let's think step by step)
	python music/melodies/query.py \
		--model $MODEL \
		--exp_dir $EXP_NAME \
		--chain_of_thought \
		--is_control

	python music/melodies/eval.py \
		--model $MODEL \
		--exp_dir $EXP_NAME \
		--chain_of_thought \
		--is_control

	############# TASK ############
	# no COT
	python music/melodies/query.py \
		--model $MODEL \
		--exp_dir $EXP_NAME

	python music/melodies/eval.py \
		--model $MODEL \
		--exp_dir $EXP_NAME

	# with chain of thought (let's think step by step)
	python music/melodies/query.py \
		--model $MODEL \
		--exp_dir $EXP_NAME \
		--chain_of_thought

	python music/melodies/eval.py \
		--model $MODEL \
		--exp_dir $EXP_NAME \
		--chain_of_thought
done

import aiohttp
import asyncio
import json
import os
import pickle
from math import ceil, log2
from random import random

import anthropic
import google.api_core.exceptions as palm_exceptions
import google.generativeai as palm
import openai
from tqdm.asyncio import tqdm_asyncio

openai_initialized = False
ANTHROPIC_CLIENT = None
palm_initialized = False

HISTORY_FILE = "history.jsonl"
CACHE_FILE = "query_cache.pkl"
OPENAI_REFRESH_QUOTA = 60
OPENAI_EXP_CAP = int(ceil(log2(OPENAI_REFRESH_QUOTA)))
PALM_MAX_CANDIDATE_COUNT = 8
BATCH_SIZE = 300  # sometimes APIs complain if we too many concurrent requests


async def query_openai(
    prompt,
    model_name,
    system_msg=None,
    history=None,
    max_tokens=None,
    temperature=0,
    retry=100,
    n=1,
    **kwargs,
):
    # reference: https://github.com/ekinakyurek/mylmapis/blob/b0adb192135898fba9e9dc88f09a18dc64c1f1a9/src/network_manager.py
    messages = []
    if system_msg is not None:
        messages += [{"role": "system", "content": system_msg}]
    messages += [{"role": "user", "content": prompt}]
    if history is not None:
        messages = history + messages
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    kwargs["temperature"] = temperature
    kwargs["n"] = n

    for i in range(retry + 1):
        wait_time = (1 << min(i, OPENAI_EXP_CAP)) + random() / 10
        try:
            response = await openai.ChatCompletion.acreate(
                model=model_name, messages=messages, **kwargs
            )
            with open(HISTORY_FILE, "a") as f:
                f.write(json.dumps((model_name, messages, kwargs, response)) + "\n")
            if any(choice["finish_reason"] != "stop" for choice in response["choices"]):
                print("Truncated response!")
                print(response)
            contents = [choice["message"]["content"] for choice in response["choices"]]
            if n == 1:
                return contents[0]
            else:
                return contents
        except (
            openai.error.APIError,
            openai.error.TryAgain,
            openai.error.Timeout,
            openai.error.APIConnectionError,
            openai.error.ServiceUnavailableError,
            openai.error.RateLimitError,
        ) as e:
            if i == retry:
                raise e
            else:
                await asyncio.sleep(wait_time)


async def query_anthropic(
    prompt,
    model_name,
    #    max_tokens=9000,
    max_tokens=250,
    temperature=0,
    retry=100,
    **kwargs,
):
    messages = [{"role": "user", "content": prompt}]
    if max_tokens is None:
        max_tokens = 9000
    kwargs["max_tokens"] = max_tokens
    kwargs["temperature"] = temperature

    for i in range(retry + 1):
        wait_time = (1 << min(i, OPENAI_EXP_CAP)) + random() / 10
        try:
            response = await ANTHROPIC_CLIENT.acompletion(
                prompt=f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
                stop_sequences=[anthropic.HUMAN_PROMPT],
                model=model_name,
                max_tokens_to_sample=max_tokens,
                temperature=temperature,
            )
            with open(HISTORY_FILE, "a") as f:
                f.write(json.dumps((model_name, messages, kwargs, response)) + "\n")
            if response["stop_reason"] != "stop_sequence":
                print("Truncated response!")
                print(response)
            return response["completion"].lstrip()
        except (anthropic.api.ApiException, aiohttp.client_exceptions.ClientConnectorError) as e:
            if i == retry:
                raise e
            else:
                await asyncio.sleep(wait_time)


async def query_palm(
    prompt,
    model_name,
    #    max_tokens=9000,
    max_tokens=250,
    temperature=0,
    retry=100,
    **kwargs,
):
    messages = [{"author": "user", "content": prompt}]
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    kwargs["temperature"] = temperature
    candidate_count = 1

    for i in range(retry + 1):
        wait_time = (1 << min(i, OPENAI_EXP_CAP)) + random() / 10
        try:
            response = palm.generate_text(
                prompt=prompt,
                model=model_name,
                max_output_tokens=max_tokens,
                temperature=temperature,
                candidate_count=candidate_count,
            )
            if not response.candidates and candidate_count < PALM_MAX_CANDIDATE_COUNT:
                candidate_count *= 2
                continue
            with open(HISTORY_FILE, "a") as f:
                f.write(json.dumps((model_name, messages, kwargs, response.to_dict())) + "\n")
            return response.candidates[0]["output"] if response.candidates else ""
        except (
            palm_exceptions.ResourceExhausted,
            palm_exceptions.ServiceUnavailable,
            palm_exceptions.InvalidArgument,
        ) as e:
            if i == retry:
                raise e
            else:
                await asyncio.sleep(wait_time)


def query_batch_wrapper(fn, prompts, *args, **kwargs):
    # I have never used asyncio and have no idea if this a sane way to do this, but it works
    async def _query(prompts):
        async_responses = [fn(prompt, *args, **kwargs) for prompt in prompts]
        return await tqdm_asyncio.gather(*async_responses)

    all_results = []
    for start in range(0, len(prompts), BATCH_SIZE):
        prompts_batch = prompts[start : start + BATCH_SIZE]
        all_results.extend(asyncio.run(_query(prompts_batch)))
    return all_results


def escape(s):
    return s.encode("unicode_escape").decode("utf-8")


def unescape(s):
    return s.encode("utf-8").decode("unicode_escape")


def query_batch(
    prompts,
    model_name,
    system_msg=None,
    history=None,
    max_tokens=None,
    temperature=0,
    retry=100,
    num_beams=1,
    skip_cache=False,
    n=1,
    **openai_kwargs,
):
    cache = {}
    if not skip_cache and os.path.exists(CACHE_FILE):
        cache = pickle.load(open(CACHE_FILE, "rb"))

    # sorry this is ugly, but for backward compatibility
    prompt2key = lambda p: (
        p,
        model_name,
        system_msg,
        tuple(history) if history is not None else None,
        max_tokens,
        temperature,
        num_beams,
    ) if n == 1 else (
        p,
        model_name,
        system_msg,
        tuple(history) if history is not None else None,
        max_tokens,
        temperature,
        num_beams,
        n,
    )

    unseen_prompts = set()
    for prompt in prompts:
        key = prompt2key(prompt)
        if key not in cache:
            unseen_prompts.add(prompt)
    unseen_prompts = list(unseen_prompts)

    if len(unseen_prompts) > 0:
        if model_name in {"gpt-3.5-turbo-0301", "gpt-4-0314"}:
            if not openai_initialized:
                openai.api_key = os.environ["OPENAI_API_KEY"]
            responses = query_batch_wrapper(
                query_openai,
                unseen_prompts,
                model_name,
                system_msg,
                history,
                max_tokens,
                temperature,
                retry,
                n,
                **openai_kwargs,
            )
        elif model_name in {"claude-v1.3"}:
            assert system_msg is None and history is None
            global ANTHROPIC_CLIENT
            if ANTHROPIC_CLIENT is None:
                ANTHROPIC_CLIENT = anthropic.Client(os.environ["ANTHROPIC_API_KEY"])
            if n > 1:
                num_prompts = len(unseen_prompts)
                orig_unseen_prompts = unseen_prompts
                unseen_prompts = [prompt for prompt in unseen_prompts for _ in range(n)]
            responses = query_batch_wrapper(
                query_anthropic,
                unseen_prompts,
                model_name,
                max_tokens,
                temperature,
                retry,
                **openai_kwargs,
            )
            if n > 1:
                responses = [responses[i : i + n] for i in range(0, len(responses), n)]
                assert len(responses) * n == num_prompts * n == sum(len(r) for r in responses) == len(unseen_prompts)
                unseen_prompts = orig_unseen_prompts
        elif model_name in {"models/text-bison-001"}:
            assert system_msg is None and history is None
            if not palm_initialized:
                palm.configure(api_key=os.environ["PALM_API_KEY"])
            if n > 1:
                num_prompts = len(unseen_prompts)
                orig_unseen_prompts = unseen_prompts
                unseen_prompts = [prompt for prompt in unseen_prompts for _ in range(n)]
            responses = query_batch_wrapper(
                query_palm,
                unseen_prompts,
                model_name,
                max_tokens,
                temperature,
                retry,
                **openai_kwargs,
            )
            if n > 1:
                responses = [responses[i : i + n] for i in range(0, len(responses), n)]
                assert len(responses) * n == num_prompts * n == sum(len(r) for r in responses) == len(unseen_prompts)
                unseen_prompts = orig_unseen_prompts
        else:
            raise NotImplementedError

        # Reload cache for better concurrency. Otherwise multiple query processes can overwrite
        # each other
        cache = {}
        if not skip_cache:
            if os.path.exists(CACHE_FILE):
                cache = pickle.load(open(CACHE_FILE, "rb"))
        for prompt, response in zip(unseen_prompts, responses, strict=True):
            key = prompt2key(prompt)
            cache[key] = response
        if not skip_cache:
            pickle.dump(cache, open(CACHE_FILE, "wb"))

    interactions_save_path = os.environ.get("INTERACTIONS_SAVE_PATH")
    if interactions_save_path is not None:
        assert not os.path.exists(interactions_save_path)
        with open(interactions_save_path, "w") as f:
            for prompt in prompts:
                key = prompt2key(prompt)
                assert isinstance(cache[key], (str, list))
                f.write(
                    escape(prompt)
                    + "\t"
                    + escape(str(cache[key]))
                    + "\t"
                    + str(isinstance(cache[key], list))
                    + "\t"
                    + "\t".join([escape(str(x)) if x is not None else "None" for x in key[1:]])
                    + "\n"
                )

    return [cache[prompt2key(prompt)] for prompt in prompts]

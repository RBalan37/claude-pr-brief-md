## Goal

Build and validate an end-to-end feedback loop for running ML experiments and evaluating them reliably, establishing a consistent process the team can reuse.

## TLDR

Build a reliable experiment/evaluation feedback loop / ML dev process. Start by doing some initial setup tasks, obtain baseline performance metrics on the QA test set and dev test set with two candidate base models, and enable running experiments.

## The Feedback Loop

The feedback loop is the full path a model improvement idea takes from an experiment to production and back. It starts with an experiment, gets evaluated on progressively stricter test sets (dev test set, then QA test set, then testers), and only a small fraction of experiments make it through each stage until reaching real clients, whose anecdotal feedback then feeds new experiments back into the loop.

**Experiment definition**: An experiment in ML is any change that affects the model's results, not necessarily a retraining. Changing a prompt is an experiment, so is swapping a model, quantizing it, changing the engine/pipeline, changing a config, or finetuning.

1. **Experiment (5% of time)**: deciding what to change in the model (HPs, prompt, etc...) and defining the experiment.
3. **Dev test (80% of time)**: once the change is made, it's run through eval on the dev test set. This is where most iteration happens, and where performance metrics need to be checked for every run, including against the baselines, not just at the end. If results aren't satisfactory, go back to phase 1.
4. **QA test / golden set (15% of time)**: experiments that look promising on dev test ( ~10%) move to QA. Once a model reaches satisfactory dev test results, it's tested against the QA dataset, an unbiased holdout, so we get a fair view of the model's behaviour on different data.
5. **Client Deployment (Experiment)**: experiments that pass QA (~1%) reach the pilot customer's QA team in a closed environment. If the model reaches satisfactory results on QA, it's ready for the client to evaluate and provide feedback. If that feedback indicates something needs to change, go back to phase 1.
6. **Prod**: <0.5% of experiments make it to full client production deployment. If the pilot customer's QA team is also satisfied, the model can be pushed to prod, where the client provides **Client Feedback** (anecdotal). This feedback should be correctly interpreted and used to create the next experiment if need be.

## Setup Before Experimenting

- Remove hard/easy balancing in the finetuning dataset, keep sample distribution as is.
- Check QA's own hard/easy balancing.
- Remove QA samples from the finetuning dataset (train/val/test).
- Create a Prompt ID, logged to MLFlow alongside the raw prompt text, so runs are traceable.

## Baselines

- Add the two candidate base models — **Aurora** (text) and **Vista** (vision) — to the eval platform.
- Get performance metrics on the different test sets (dev test and QA), for both Aurora base and Vista base. This is where most iteration time (~90%) will go, comparing experiments against these baselines.
- Basically, 4 runs: Aurora on dev test, Aurora on QA, Vista on dev test, Vista on QA.

## Experiments

Once setup and baselines are in place:

- 1st experiment: **Aurora prompt tuning** -> take the Aurora base model and try out different prompts to get the best performance on the dev test.
  - Improve task explanation in the prompt.
  - Add structural info: table type, column (future), row, header.
- 2nd experiment: **Finetune baseline run** -> train a model without train set balancing, and with a lower LR (1E-4 to 7E-5).

## Impacts

Production impact Level - None
Development impact Level - Low

Will affect the ML dev/eval workflow, changes to the experiment pipeline and evaluation (internal eval dashboard) might happen, old version will be fully replaced. Only devs working on model development will be impacted, so low impact.

No production changes, so no impact.

## Challenges

- Creating the baselines will be time consuming, for both dev sets and models.
- Making it easy to detect possible performance bottlenecks and blind spots early.

# Gates: Compart Frontier 1-3 Verification & Benchmark Engine

> Frozen historical record (pre-rename milestones). CHECK lines below reference
> the old `compart` CLI, since-removed `trials`/`reproduce` commands, and a
> developer-local absolute path — they are evidence of what passed at the time,
> not runnable instructions. Current verification is `scripts/run_all_tests.py`.

Scope: Build Dynamic Spec-Driven Route Synthesizer (Frontier 1), Surgical AST Patcher (Frontier 2), and Compart Trials Benchmark Suite (Frontier 3) with precision metrics, Python CLI integration, and zero regressions.

- [x] G1: Dynamic Spec-Driven Route Synthesizer compiles and passes tests
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib resolver 2>&1 | tail -3
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 16 passed; 0 failed; 0 ignored; 0 measured; 496 filtered out; finished in 0.00s

- [x] G2: Surgical AST Patcher compiles and passes unit tests (`src/engines/autopatch/patcher.rs`)
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib patcher 2>&1 | tail -3
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 507 filtered out; finished in 0.00s

- [x] G3: Compart Trials benchmark engine compiles and passes tests (`src/engines/autopatch/trials.rs`)
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib trials 2>&1 | tail -3
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 510 filtered out; finished in 0.01s

- [x] G4: PyO3 FFI bindings compile and expose new functions in _core module
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo check --features pyo3-binding 2>&1 | tail -3
  EXPECT: Finished
  EVIDENCE: Checking compart-core v1.0.4 (/Users/tanmaydevare/Tanmay/Agent/compart) | Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.59s

- [x] G5: Python SDK and CLI tests pass including test_cli_trials and test_cli_patch
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -m pytest tests/test_autopatch_sdk.py tests/test_autopatch_cli.py 2>&1 | tail -3
  EXPECT: passed
  EVIDENCE: ============================== 17 passed in 0.20s ==============================

- [x] G6: CLI command `compart trials` runs canonical migration cases and outputs precision leaderboard
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -m compart.cli.main trials 2>&1 | grep "COMPART TRIALS BENCHMARK"
  EXPECT: COMPART TRIALS BENCHMARK
  EVIDENCE: COMPART TRIALS BENCHMARK LEADERBOARD

- [x] G7: Zero emojis in codebase (enforces clinical enterprise standard)
  CHECK: python3 -c 'import os, re; e=re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]"); errs=[f for r,_,fs in os.walk("src") for f in fs if f.endswith(".rs") and e.search(open(os.path.join(r,f),errors="ignore").read())]; print("CLEAN" if not errs else f"FAIL: {errs}")'
  EXPECT: CLEAN
  EVIDENCE: CLEAN

- [x] G8: Full Rust test suite passes with 0 failures
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 524 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.11s

- [x] G9: Typed uncertainty taxonomy exists with 10+ distinct reasons
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib uncertainty_reason_taxonomy_has_at_least_ten_variants 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G10: Safety policy blocks unverified patches from mergeable PR output
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib policy_blocks_unresolved_references 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G11: Historical benchmark harness runs with 3+ verified cases
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib trials_v2::tests::trials_v2_runs_and_distinguishes_verified_from_rejected 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G12: Unverified cases are classified and excluded from official scores
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -c 'from compart import autopatch; r=autopatch.run_trials_v2(); assert r["rejected_unverified_cases"] >= 1; print("EXCLUDED_OK")'
  EXPECT: EXCLUDED_OK
  EVIDENCE: EXCLUDED_OK

- [x] G13: Network trace contract matcher supports parameterized paths
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib trace::tests::correlates_traces_with_parameter_templates 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G14: Redaction eliminates API keys/tokens from stored traces
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib trace::tests::redacts_token_patterns_even_with_neutral_keys 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G15: Behavioral verifier detects test breakages on modified files
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib verification::tests::quarantines_patch_if_tests_fail 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G16: False positive rate on unrelated methods in affected files is <= 5%
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -m pytest tests/test_autopatch_sdk.py -k test_false_positive_regressions 2>&1 | grep "passed"
  EXPECT: passed
  EVIDENCE: 1 passed, 10 deselected in 0.15s

- [x] G17: Detection recall on breaking operations is >= 95%
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -c 'from compart import autopatch; r=autopatch.run_trials_v2(); assert r["overall_detection_recall"] >= 0.95; print("RECALL_OK")'
  EXPECT: RECALL_OK
  EVIDENCE: RECALL_OK

- [x] G18: Trust report clearly separates confirmed, unaffected, and unresolved callsites
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib report::tests::trust_report_renders_three_tiers 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 523 filtered out; finished in 0.00s

- [x] G19: Historical replay engine executes LangChain OpenAI v4 case with zero blast radius
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib replay::tests::replay_runs_langchain_openai_case 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 525 filtered out; finished in 0.01s

- [x] G20: Historical replay engine executes Cal.com Stripe v13 case with verified test repair and zero blast radius
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib replay::tests::replay_runs_calcom_stripe_case 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 525 filtered out; finished in 0.01s

- [x] G21: Compart CLI supports `reproduce` subcommand across verified real-world cases
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -m compart.cli.main reproduce all --json 2>&1 | grep "langchain-openai-v4"
  EXPECT: langchain-openai-v4
  EVIDENCE: "case_id": "langchain-openai-v4",

- [x] G22: Python test suite validates replay engine with zero regressions
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -m pytest tests/test_autopatch_replay.py 2>&1 | grep "passed"
  EXPECT: passed
  EVIDENCE: 3 passed in 0.13s

- [x] G23: Standalone reproduction script `./scripts/reproduce_ground_truth.sh` runs successfully
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && ./scripts/reproduce_ground_truth.sh 2>&1 | grep "Replay protocol successfully completed"
  EXPECT: Replay protocol successfully completed
  EVIDENCE: Replay protocol successfully completed with verified zero blast radius.

- [x] G24: Empirical replay verification dossier documents flagship cases, invariants, and reproduction roadmap
  CHECK: test -f docs/benchmarks/HISTORICAL_REPLAY.md && echo "DOSSIER_EXISTS"
  EXPECT: DOSSIER_EXISTS
  EVIDENCE: DOSSIER_EXISTS

- [x] G25: Full-Repo Git Replay engine executes with fail-closed live verification and semantic diff comparison
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && PYTHONPATH=python python3 -m pytest tests/test_autopatch_replay.py -k test_full_git_replay_three_flagship_cases 2>&1 | grep "passed"
  EXPECT: passed
  EVIDENCE: 1 passed in 0.14s

- [x] G26: Exact manifest and lockfile resolution engine with cryptographic BLAKE3 evidence bundle verification
  CHECK: cd /Users/tanmaydevare/Tanmay/Agent/compart && cargo test --lib manifest_lockfile 2>&1 | grep "test result: ok"
  EXPECT: test result: ok
  EVIDENCE: test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 532 filtered out; finished in 0.00s





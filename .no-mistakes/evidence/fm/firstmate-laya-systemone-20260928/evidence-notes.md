# Optional Laya provider live validation

The real Firstmate resolver ran against an unmodified canonical Laya v0.3.21 server and its public English checkpoint on CPU. Dependencies, runtime libraries, model cache, configuration and test homes were disposable and workspace-local. Operator homes and credentials were not used.

Canonical inference returned rule_1 probability 0.5492 and confidence 0.007. The existing global confidence floor correctly returned ambiguous without a profile. Explicitly configuring the rule with min_confidence 0.5 returned Codex gpt-6.1-sol medium, with and without bearer authentication. This verifies protocol compatibility and boundaries, not routing quality or performance.

An HTTP proxy forwarded and captured canonical inference. Controlled responses exercised HTTP-500, malformed-response, confidence, approval, quota-floor, exhausted-quota and tie cases against the real resolver. quota-axi served a disposable schema-5 snapshot instead of operator accounts. Only canonical inference scenarios establish real Laya model compatibility.

Requests omitted rule rationale, profiles, quota and unrelated brief sections. Secrets were absent from real curl argv and environment. Unsafe URLs, CR/LF keys, unsupported providers and unverified profiles were rejected before HTTP. Default-off, precedence and never-send cases made no requests. Connection refusal and canonical authentication refusal returned error without a profile.

The actual bootstrap executable ran in local detection-only mode against isolated homes. It validated typed fields with Laya selected and no TypeSafe key, and preserved default-off and environment precedence.

Targeted baseline checks passed: bash tests/fm-dispatch-resolve.test.sh; test_crew_dispatch_validation extracted into a temporary same-directory harness with FM_TEST_BASE_PATH set to the available PATH. Empty bootstrap fixture homes emitted unrelated git-not-a-repository stderr; dispatch assertions passed.

The disposable server and all transient workspace files were removed after validation. No permanent source or test edits were made.

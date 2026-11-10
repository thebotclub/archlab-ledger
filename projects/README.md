# projects/ - ArchLab Studio seals

Each `projects/<id>/` folder holds the public seals of one ArchLab Studio project:

- `seal-1.commit.json` - commitment to the pre-registration (predictions, seeds, controls, decision-script hash), made BEFORE any harness code exists.
- `seal-2.commit.json` - commitment to the built harness (git tree hash), container image digest, eval data hash and mechanical-check outputs, made BEFORE any full run.
- `*.tsr` - RFC 3161 timestamp tokens over the commitment from two independent TSAs (verify: `openssl ts -reply -in X.tsr -text`).
- `*.ots` - OpenTimestamps proof (Bitcoin-anchored; `ots upgrade` then `ots verify`).

The commitment is `sha256(salt || canonical_json(seal))`. The salt and the seal contents are revealed when the owner publishes the project; anyone can then recompute the commitment. This branch is protected: no force-push, no deletion, linear history.

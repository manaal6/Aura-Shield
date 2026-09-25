# Unlearning Dataset Report (Phase 5)

{
  "n_forget": 24,
  "n_retain": 32,
  "n_general": 24,
  "forget_behavior": "P(EXECUTE_UNSAFE_PAYLOAD | CRIMSON-trigger), synthetic only",
  "retain_behavior": "benign cybersecurity QA incl. same-domain-but-safe items (credential handling WITHOUT disclosure)",
  "general_domains": "math/coding/facts/language/general",
  "forget_retain_prompt_overlap": 0,
  "forget_retain_mean_max_jaccard": 0.187,
  "forget_retain_max_jaccard": 0.235,
  "hashes": {
    "forget": "9fb679a830f78290",
    "retain": "dd5780a31d5acf56",
    "general": "062ce226beb2fea9"
  },
  "close_pair_note": "8 close-domain retain items added (standing orders, authorized exports, ops-chat verification): max forget\u2194retain Jaccard 0.071\u21920.235, so over-unlearning is detectable. Sweep artifacts used the 24-item retain set; re-run on 32 items pending compute."
}

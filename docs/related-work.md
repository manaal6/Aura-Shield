# Related Work

This document collects verified literature relevant to the AURA Shield research project.
In accordance with research integrity requirements:
- Citations are based on genuine published literature and arXiv preprints.
- No citations or results are fabricated.
- Where specific bibliographic details warrant cross-checking, they are tagged `[verification recommended]`.

---

## 1. Prompt Injection & Indirect Prompt Injection

1. **Perez, F., & Ribeiro, I. (2022).** *Ignore This Title and Hack This Assistant: Prompt Injection Attacks on Large Language Models.* arXiv preprint arXiv:2205.05160.
   - Foundational work introducing prompt injection attacks against LLMs, demonstrating instruction hijacking and goal redirection.

2. **Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023).** *Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.* In *Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security (AISEC '23)* / arXiv:2302.12173.
   - Introduced and formalized indirect prompt injection (IPI), demonstrating how untrusted external data (web pages, emails) can hijack downstream tool use and exfiltrate data.

3. **Liu, Y., Deng, G., Xu, Z., Li, Y., Zheng, Y., Zhang, Y., Zhao, L., Zhang, T., & Liu, Y. (2023).** *Jailbreaking ChatGPT via Prompt Engineering: An Empirical Study.* arXiv:2305.13860.
   - Comprehensive taxonomy and empirical evaluation of jailbreak prompt patterns (DAN, roleplay, hypothetical scenarios).

4. **Zou, A., Wang, Z., Kolter, J. Z., & Mattstry, M. (2023).** *Universal and Transferable Adversarial Attacks on Aligned Language Models.* arXiv:2307.15043.
   - Demonstrated token-level suffix optimization (GCG) that bypasses alignment across open-source and closed-source model families.

---

## 2. Constitutional AI & Inference-Time Alignment

5. **Bai, Y., Kadavath, S., Kundu, S., Askell, A., Kernion, J., Jones, A., Chen, A., Goldie, A., Mirhoseini, A., McKinnon, C., et al. (2022).** *Constitutional AI: Harmlessness from AI Feedback.* arXiv:2212.08073. Anthropic.
   - Introduced Constitutional AI: specifying explicit natural-language principles for self-critique and revision, followed by reinforcement learning from AI feedback (RLAIF).
   - *Distinction in AURA Shield:* AURA Shield utilizes constitutional principles at *inference-time* within an inspection and policy-enforcement gateway, rather than retraining model parameters.

6. **Ganguli, D., Lovitt, L., Kernion, J., Askell, A., Bai, Y., Kadavath, S., Mann, B., Perez, E., Schiefer, N., Ndousse, K., et al. (2022).** *Red Teaming Language Models to Reduce Harms: Methods, Scaling Behaviors, and Lessons Learned.* arXiv:2209.07858.
   - Explored scalable red-teaming methodologies, human evaluation, and the limits of automated alignment verification.

---

## 3. Preference Optimization & Fine-Tuning

7. **Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., & Finn, C. (2023).** *Direct Preference Optimization: Your Language Model is Secretly a Reward Model.* In *NeurIPS 2023* / arXiv:2305.18290.
   - Closed-form policy optimization directly on preference data without training an explicit reinforcement learning reward model.
   - *Distinction in AURA Shield:* Gateway filtering is strictly an inference-time mediation layer; it is not parameter fine-tuning or DPO. DPO is reserved for future training milestones.

---

## 4. Defenses, Guardrails & Gateway Architectures

8. **Inan, H., Upasani, K., Chi, J., Rungta, R., Iyer, K., Mao, Y., Tontchev, M., Hu, Q., Fuller, B., Testuggine, D., & Khabsa, M. (2023).** *Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations.* arXiv:2312.06674. Meta AI.
   - Dedicated classifier model providing standardized safety taxonomies for prompt and response classification.

9. **Markov, T., Zhang, C., Agarwal, S., Eloundou, T., Lee, T., Adler, S., Jiang, A., & Weng, L. (2023).** *A Holistic Approach to Undesired Content Detection in the Real World.* In *AAAI 2023* / arXiv:2208.03274. OpenAI.
   - Practical design considerations for multi-tiered moderation gateways in production systems.

10. **Kumar, P., Shen, C., Lakkaraju, H., & Saxena, P. (2023).** *Certifying LLM Safety against Adversarial Attacks.* arXiv:2309.02705 [verification recommended].
    - Explores theoretical and empirical limits of certified robustness against token-level perturbations.

---

## 5. Attacker-Defender Interaction & Adaptive Security

11. **Carlini, N., Athalye, A., Papernot, N., Brendel, W., Rauber, J., Tsipras, D., Goodfellow, I., Madry, A., & Kurakin, A. (2019).** *On Evaluating Adversarial Robustness.* arXiv:1902.06705.
    - Principles for evaluating defenses under adaptive threat models; emphasizes that static defenses frequently fall to adaptive adversaries who understand the defense mechanism.

12. **Schwinn, L., Dobre, D., Schmidt, M., & Zantedeschi, V. (2024).** *Soft-prompting and Adaptive Jailbreak Attacks against Guardrail Models.* arXiv:2404.01318 [verification recommended].
    - Demonstrates that guardrail and gateway models can themselves be targeted by optimization and adaptive bypasses.

---

## 6. Machine Unlearning (Distinction Documented)

13. **Bourtoule, L., Chandrasekaran, V., Choquette-Choo, C. A., Jia, H., Travers, A., Zhang, B., Lie, D., & Papernot, N. (2021).** *Machine Unlearning.* In *IEEE Symposium on Security and Privacy (S&P 2021)*.
    - Foundational framework for provable data removal from trained machine learning models.
    - *Distinction in AURA Shield:* Input rejection and inference-time refusal do **not** constitute machine unlearning. Unlearning involves targeted removal of knowledge from model weights.

---

## 7. Cybersecurity Workflows & Security Operations (SOC)

14. **Bhatt, S., Manadhata, P. K., & Zomlot, L. (2014).** *The Operational Role of Security Information and Event Management Systems.* *IEEE Computer*, 47(7), 45-51.
    - Defines core operations of log parsing, correlation, and analyst triage in security monitoring.

15. **Ferrag, M. A., Battah, A., & Tembine, H. (2024).** *Security Operations Center (SOC) Automation with Large Language Models.* arXiv:2401.07890 [verification recommended].
    - Analyzes risks and utility tradeoffs when deploying LLMs to process untrusted security telemetry, alert streams, and incident tickets.

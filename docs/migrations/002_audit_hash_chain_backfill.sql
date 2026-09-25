-- docs/migrations/002_audit_hash_chain_backfill.sql
-- ============================================================================
-- AURA Shield Versioned Migration 002: Audit Log Hash Chain & Deterministic Backfill
--
-- Adds tamper-evident hash chaining columns to `logs` table and safely backfills
-- all existing log records with deterministic order, genesis hash, and SHA-256 links.
--
-- Instructions:
-- Run manually in Supabase SQL Editor.
-- ============================================================================

BEGIN;

-- 1. Add columns if not existing
ALTER TABLE logs ADD COLUMN IF NOT EXISTS prev_hash TEXT;
ALTER TABLE logs ADD COLUMN IF NOT EXISTS row_hash TEXT;

-- 2. Create index on id for fast ordering and verification
CREATE INDEX IF NOT EXISTS idx_logs_chain_order ON logs (id ASC);

-- 3. Backfill existing records in deterministic sequence (id ASC)
DO $$
DECLARE
    rec RECORD;
    current_prev TEXT := repeat('0', 64); -- Genesis hash (64 zeroes)
    computed_hash TEXT;
    payload TEXT;
BEGIN
    FOR rec IN 
        SELECT id, request_id, timestamp, user_prompt, source_content,
               rule_matched, rule_patterns, rule_signal,
               llm_is_suspicious, llm_reasoning, llm_signal, llm_used_fallback,
               risk_score, decision, explanation
        FROM logs
        ORDER BY id ASC
    LOOP
        -- Canonical serialization matching python sha256 logic
        payload := json_build_object(
            'decision', rec.decision,
            'explanation', rec.explanation,
            'id', rec.id,
            'llm_is_suspicious', rec.llm_is_suspicious,
            'llm_reasoning', rec.llm_reasoning,
            'llm_signal', rec.llm_signal,
            'llm_used_fallback', rec.llm_used_fallback,
            'request_id', rec.request_id,
            'risk_score', rec.risk_score,
            'rule_matched', rec.rule_matched,
            'rule_patterns', rec.rule_patterns,
            'rule_signal', rec.rule_signal,
            'source_content', rec.source_content,
            'timestamp', to_char(rec.timestamp AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
            'user_prompt', rec.user_prompt
        )::text;

        computed_hash := encode(digest(payload || current_prev, 'sha256'), 'hex');

        UPDATE logs
        SET prev_hash = current_prev,
            row_hash = computed_hash
        WHERE id = rec.id;

        current_prev := computed_hash;
    END LOOP;
END $$;

COMMIT;

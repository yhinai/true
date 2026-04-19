-- CBC auto-remediation queue + trigger.
-- Idempotent: safe to run multiple times.
--
-- Enqueues a row in `cbc_remediations` whenever a `cbc_runs` row lands with
-- a failing verdict (FALSIFIED or TIMED_OUT). A separate dispatcher (see
-- `scripts/remediate_dispatcher.py`) drains the queue and fires the
-- `cbc-remediate.yml` GitHub Actions workflow.

-- ---------------------------------------------------------------------------
-- Queue table
-- ---------------------------------------------------------------------------
create table if not exists cbc_remediations (
    id             bigserial primary key,
    run_id         text not null,
    task_id        text not null,
    task_path      text not null,
    status         text not null default 'queued'
        check (status in ('queued','running','merged','bailed_budget','bailed_loop','error')),
    triggered_by   text default 'supabase_trigger',
    attempts_used  int default 0,
    cost_usd       numeric(10,4) default 0,
    pr_url         text,
    new_run_id     text,
    error          text,
    created_at     timestamptz not null default now(),
    started_at     timestamptz,
    completed_at   timestamptz,
    unique (run_id)  -- never remediate the same failed run twice
);

create index if not exists cbc_remediations_status_idx
    on cbc_remediations (status);
create index if not exists cbc_remediations_run_idx
    on cbc_remediations (run_id);
create index if not exists cbc_remediations_created_idx
    on cbc_remediations (created_at desc);

-- ---------------------------------------------------------------------------
-- Optional task_id -> task_path mapping.
-- If a row for NEW.task_id exists, its task_path wins. Otherwise the trigger
-- falls back to the convention `fixtures/oracle_tasks/<task_id>/task.yaml`.
-- ---------------------------------------------------------------------------
create table if not exists cbc_tasks (
    task_id    text primary key,
    task_path  text not null,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Enqueue function
-- ---------------------------------------------------------------------------
create or replace function cbc_enqueue_remediation()
returns trigger
language plpgsql
as $$
declare
    resolved_path text;
begin
    -- Resolve task_path: explicit mapping first, convention fallback second.
    select task_path into resolved_path
    from cbc_tasks
    where task_id = new.task_id;

    if resolved_path is null then
        resolved_path := 'fixtures/oracle_tasks/' || coalesce(new.task_id, 'unknown') || '/task.yaml';
    end if;

    insert into cbc_remediations (run_id, task_id, task_path, status, triggered_by)
    values (new.run_id, coalesce(new.task_id, 'unknown'), resolved_path, 'queued', 'supabase_trigger')
    on conflict (run_id) do nothing;

    return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Trigger on cbc_runs: fires only on failing verdicts.
-- ---------------------------------------------------------------------------
drop trigger if exists cbc_runs_enqueue_remediation on cbc_runs;

create trigger cbc_runs_enqueue_remediation
after insert or update on cbc_runs
for each row
when (new.verdict in ('FALSIFIED','TIMED_OUT'))
execute function cbc_enqueue_remediation();

-- ---------------------------------------------------------------------------
-- Optional: direct pg_net dispatch (documented, NOT enabled here).
-- The GitHub token must never live in a migration. If you want the DB to
-- fire the workflow itself, enable the `pg_net` extension, store the token
-- in Vault, and replace the dispatcher poller with a call like:
--
--   select net.http_post(
--       url     := 'https://api.github.com/repos/<owner>/<repo>/actions/workflows/cbc-remediate.yml/dispatches',
--       headers := jsonb_build_object(
--           'Accept',        'application/vnd.github+json',
--           'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name = 'GH_TOKEN'),
--           'Content-Type',  'application/json'
--       ),
--       body    := jsonb_build_object(
--           'ref', 'main',
--           'inputs', jsonb_build_object(
--               'task_path',      new_row.task_path,
--               'remediation_id', new_row.id::text
--           )
--       )
--   );
--
-- Leave the dispatch to `scripts/remediate_dispatcher.py` by default.
-- ---------------------------------------------------------------------------

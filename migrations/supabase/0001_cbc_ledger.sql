-- CBC ledger mirror schema for Supabase/Postgres.
-- Idempotent: safe to run multiple times.

create table if not exists cbc_runs (
    run_id          text primary key,
    task_id         text,
    title           text,
    mode            text,
    verdict         text,
    adapter         text,
    started_at      timestamptz,
    ended_at        timestamptz,
    payload         jsonb       not null,
    inserted_at     timestamptz not null default now()
);

create index if not exists cbc_runs_task_idx     on cbc_runs (task_id);
create index if not exists cbc_runs_verdict_idx  on cbc_runs (verdict);
create index if not exists cbc_runs_started_idx  on cbc_runs (started_at desc);

create table if not exists cbc_run_events (
    id          bigserial primary key,
    run_id      text not null references cbc_runs(run_id) on delete cascade,
    seq         integer not null,
    kind        text    not null,   -- e.g. "attempt", "verify", "stdout"
    payload     jsonb   not null,
    emitted_at  timestamptz not null default now(),
    unique (run_id, seq)
);

create index if not exists cbc_run_events_run_idx on cbc_run_events (run_id, seq);

-- Optional: enable RLS. Keep disabled by default; we write with the
-- service-role key which bypasses RLS anyway. Uncomment to lock the
-- tables down for anon reads.
--
-- alter table cbc_runs       enable row level security;
-- alter table cbc_run_events enable row level security;
-- create policy "cbc_runs_read_anon"    on cbc_runs       for select using (true);
-- create policy "cbc_events_read_anon"  on cbc_run_events for select using (true);

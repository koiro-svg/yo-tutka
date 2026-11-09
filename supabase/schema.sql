-- YO-harjoittelu: user data for cross-device sync (Supabase / Postgres).
-- Run once in Supabase → SQL Editor. Safe to re-run (idempotent).
-- Every user can read and write ONLY their own rows (row level security).

-- Scores, assessment history, review list and exam simulations: one JSON document per user.
create table if not exists public.practice_state (
  user_id    uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  state      jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint practice_state_size check (pg_column_size(state) <= 2000000)
);

-- Answers (HTML with formula images and pasted images as data URLs), one row per answer field.
create table if not exists public.practice_answers (
  user_id uuid   not null default auth.uid() references auth.users (id) on delete cascade,
  key     text   not null check (char_length(key) <= 200),
  html    text   not null,
  at      bigint not null,
  primary key (user_id, key),
  constraint practice_answers_size check (octet_length(html) <= 1000000)
);

alter table public.practice_state   enable row level security;
alter table public.practice_answers enable row level security;

-- Signed-out visitors have no business with these tables at all (RLS would return nothing anyway).
revoke all on public.practice_state, public.practice_answers from anon;

drop policy if exists "own state"   on public.practice_state;
drop policy if exists "own answers" on public.practice_answers;
create policy "own state" on public.practice_state for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "own answers" on public.practice_answers for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

-- Per-user quota for answers: 15 MB in total (images are the big part).
create or replace function public.practice_answers_quota() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  -- runs before RLS: refuse foreign rows first, so the size check cannot be used to probe other users
  if new.user_id is distinct from (select auth.uid()) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if (select coalesce(sum(octet_length(a.html)), 0) from public.practice_answers a
       where a.user_id = new.user_id and a.key <> new.key) + octet_length(new.html) > 15000000 then
    raise exception 'answers quota exceeded' using errcode = 'P0001';
  end if;
  return new;
end $$;
drop trigger if exists practice_answers_quota on public.practice_answers;
create trigger practice_answers_quota before insert or update on public.practice_answers
  for each row execute function public.practice_answers_quota();

-- "Poista tili": the signed-in user deletes their own account; the rows above go with it (on delete cascade).
create or replace function public.delete_my_account() returns void
language sql security definer set search_path = '' as $$
  delete from auth.users where id = auth.uid();
$$;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;

-- Daily keep-alive from GitHub Actions (a free project pauses after 7 days without activity).
create or replace function public.ping() returns integer language sql stable as $$ select 1 $$;
revoke all on function public.ping() from public;
grant execute on function public.ping() to anon, authenticated;

-- Visakaksintaisto: anonymous play counts for the Suosituimmat list (/visa). No nickname or player id is stored.
create table if not exists public.visa_plays (
  quiz_id text not null check (quiz_id ~ '^[a-z0-9_-]{1,80}$'),
  day date not null default current_date,
  plays integer not null default 0,
  primary key (quiz_id, day)
);
alter table public.visa_plays enable row level security;
revoke all on public.visa_plays from anon, authenticated;

create or replace function public.visa_count_play(q text) returns void
language sql security definer set search_path = ''
as $$
  insert into public.visa_plays (quiz_id, day, plays) values (q, current_date, 1)
  on conflict (quiz_id, day) do update set plays = public.visa_plays.plays + 1;
$$;

create or replace function public.visa_trending() returns table (quiz_id text, plays bigint)
language sql stable security definer set search_path = ''
as $$
  select p.quiz_id, sum(p.plays)::bigint as plays
  from public.visa_plays p
  where p.day >= current_date - 14
  group by p.quiz_id
  order by plays desc
  limit 20;
$$;

revoke all on function public.visa_count_play(text) from public;
revoke all on function public.visa_trending() from public;
grant execute on function public.visa_count_play(text) to anon, authenticated;
grant execute on function public.visa_trending() to anon, authenticated;

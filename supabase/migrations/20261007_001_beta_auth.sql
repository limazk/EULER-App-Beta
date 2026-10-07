-- EULER Beta: identidade, aprovação, organizações e papéis.
-- Execute no SQL Editor de um projeto Supabase novo.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    full_name text not null default '',
    status text not null default 'pending'
        check (status in ('pending', 'active', 'suspended', 'rejected')),
    is_superadmin boolean not null default false,
    created_at timestamptz not null default now(),
    approved_at timestamptz,
    last_seen_at timestamptz
);

create table if not exists public.organizations (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null unique,
    status text not null default 'active'
        check (status in ('active', 'suspended')),
    created_at timestamptz not null default now()
);

create table if not exists public.memberships (
    organization_id uuid not null references public.organizations(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null default 'viewer'
        check (role in ('admin', 'engineer', 'operator', 'viewer')),
    status text not null default 'active'
        check (status in ('active', 'suspended')),
    created_at timestamptz not null default now(),
    primary key (organization_id, user_id)
);

create index if not exists memberships_user_id_idx
    on public.memberships(user_id);

create unique index if not exists memberships_one_active_org_per_user_idx
    on public.memberships(user_id)
    where status = 'active';

create or replace function public.handle_new_euler_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, email, full_name)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'full_name', '')
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

revoke execute on function public.handle_new_euler_user() from public, anon, authenticated;

drop trigger if exists on_auth_user_created_euler on auth.users;
create trigger on_auth_user_created_euler
after insert on auth.users
for each row execute procedure public.handle_new_euler_user();

alter table public.profiles enable row level security;
alter table public.organizations enable row level security;
alter table public.memberships enable row level security;

revoke all on public.profiles from anon, authenticated;
revoke all on public.organizations from anon, authenticated;
revoke all on public.memberships from anon, authenticated;

grant select on public.profiles to authenticated;
grant select on public.organizations to authenticated;
grant select on public.memberships to authenticated;

drop policy if exists "profile próprio" on public.profiles;
create policy "profile próprio"
on public.profiles for select
to authenticated
using ((select auth.uid()) = id);

drop policy if exists "membership própria" on public.memberships;
create policy "membership própria"
on public.memberships for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "organizações do usuário" on public.organizations;
create policy "organizações do usuário"
on public.organizations for select
to authenticated
using (
    exists (
        select 1
        from public.memberships m
        where m.organization_id = organizations.id
          and m.user_id = (select auth.uid())
          and m.status = 'active'
    )
);

-- Depois que SUA primeira conta for criada, rode UMA VEZ substituindo o e-mail:
-- update public.profiles
-- set status = 'active', is_superadmin = true, approved_at = now()
-- where email = 'SEU_EMAIL_AQUI';

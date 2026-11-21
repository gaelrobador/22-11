-- Pegar entero en Supabase > SQL Editor > New query > Run
-- Es idempotente: se puede correr de nuevo sin romper nada.

create table if not exists albums (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz default now()
);

create table if not exists photos (
  id uuid primary key default gen_random_uuid(),
  path text not null,
  album_id uuid references albums(id) on delete set null,  -- null = bandeja de entrada
  caption text,
  created_at timestamptz default now()
);

-- Solo usuarios logueados (o sea, ustedes dos) pueden leer/escribir
alter table albums enable row level security;
alter table photos enable row level security;
drop policy if exists "nosotros albums" on albums;
create policy "nosotros albums" on albums for all to authenticated using (true) with check (true);
drop policy if exists "nosotros photos" on photos;
create policy "nosotros photos" on photos for all to authenticated using (true) with check (true);

-- Por si el proyecto no expone tablas nuevas a la API automáticamente
grant select, insert, update, delete on albums, photos to authenticated;

-- Bucket privado para las fotos
insert into storage.buckets (id, name, public) values ('fotos', 'fotos', false)
on conflict (id) do nothing;

drop policy if exists "nosotros fotos" on storage.objects;
create policy "nosotros fotos" on storage.objects for all to authenticated
  using (bucket_id = 'fotos') with check (bucket_id = 'fotos');

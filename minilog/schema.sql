drop table if exists users;
drop table if exists categories;
drop table if exists items;

create table users (
  id integer primary key autoincrement,
  name text not null,
  email text not null,
  password text not null
);

create table categories (
  id integer primary key autoincrement,
  name text not null,
  author_id integer not null
);

create table items (
  id integer primary key autoincrement,
  name text not null,
  author_id integer not null,
  category_id integer not null
);

drop table if exists users;
create table users (
  id integer primary key autoincrement,
  email text not null,
  name text not null,
  password text not null,
  uuid text not null,
  phone text,
  room text,
  your_products text not null,
  verified integer not null
);

drop table if exists products;
create table products (
  id integer primary key autoincrement,
  name text not null,
  picture text not null,
  description text not null,
  price text not null,
  seller text not null,
  interested_people text not null,
  uuid text not null
);
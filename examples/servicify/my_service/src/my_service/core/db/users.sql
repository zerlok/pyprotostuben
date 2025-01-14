create table users
(
    id         serial primary key,
    name       varchar(256) not null,
    created_at timestamp    not null default now(),
    note       varchar(1024)
);

-- get_user_note_by_id :one
select id, note
from users
where id = :user_id;

-- insert_one_user :one
insert into users (id, name)
values (:user_id, :user_name);

-- insert_many_users :many
copy users (id, name) from stdin;

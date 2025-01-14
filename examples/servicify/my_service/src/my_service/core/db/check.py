from itertools import chain

import sqlglot
from sqlglot import MappingSchema
from sqlglot.expressions import ColumnDef, Create, Expression, Schema, Table
from sqlglot.optimizer.annotate_types import annotate_types
from sqlglot.optimizer.qualify import qualify

SQL = """
create table users
(
    id         serial primary key,
    name       varchar(256) not null,
    note       varchar(256)
);

select id, name, note
from users
where id = :user_id;

insert into users (id, name, note)
values (:user_id, :user_name, :user_note);

copy users (id, name, note) from stdin;
"""


def main() -> None:
    create_def, *queries = sqlglot.parse(sql=SQL, read="postgres")

    schema = collect_schema(create_def)

    for i, query in enumerate(queries):
        # see: https://github.com/tobymao/sqlglot/issues/4611
        print(i, repr(annotate_types(qualify(query, dialect="postgres"), schema=schema)))


def collect_schema(*exprs: Expression) -> MappingSchema:
    schema = MappingSchema(dialect="postgres")

    for expr in chain.from_iterable(qualify(expr.copy(), dialect="postgres").dfs() for expr in exprs):
        if isinstance(expr, Table) and isinstance(expr.parent, Schema) and isinstance(expr.parent.parent, Create):
            columns = {col.name: col.kind for col in expr.parent.expressions if isinstance(col, ColumnDef)}
            schema.add_table(expr, columns)

    print(schema.mapping)

    return schema


if __name__ == "__main__":
    main()

"""create tweets table

Revision ID: 20240920_create_tweets_table
Revises:
Create Date: 2024-09-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20240920_create_tweets_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tweets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tweet_id", sa.String(), unique=True),
        sa.Column("author_id", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("query", sa.String()),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("inserted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("tweets")

"""为插件广场增加评论。"""
import sqlalchemy as sa
from alembic import op

revision = "20261017_0019"
down_revision = "20261016_0018"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plugin_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("plugin_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plugin_id"], ["plugins.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["site_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plugin_comments_plugin_time",
        "plugin_comments",
        ["plugin_id", "created_at"],
    )
    op.create_index(
        "ix_plugin_comments_user_time",
        "plugin_comments",
        ["user_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_plugin_comments_user_time", table_name="plugin_comments")
    op.drop_index("ix_plugin_comments_plugin_time", table_name="plugin_comments")
    op.drop_table("plugin_comments")

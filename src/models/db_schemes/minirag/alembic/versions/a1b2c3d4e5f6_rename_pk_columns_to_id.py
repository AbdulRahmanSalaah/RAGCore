"""Rename pk columns to id to match models

Revision ID: a1b2c3d4e5f6
Revises: cd301628d888
Create Date: 2026-06-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cd301628d888'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename PK columns from *_id to id to match SQLAlchemy models."""

    # --- chunks table: drop FKs first, then rename PK, then re-add FKs ---
    op.drop_constraint('chunks_chunk_project_id_fkey', 'chunks', type_='foreignkey')
    op.drop_constraint('chunks_chunk_asset_id_fkey', 'chunks', type_='foreignkey')
    op.drop_constraint('chunks_pkey', 'chunks', type_='primary')

    op.alter_column('chunks', 'chunk_id', new_column_name='id')

    op.create_primary_key('chunks_pkey', 'chunks', ['id'])

    # --- assets table: drop FK to projects, rename PK ---
    op.drop_constraint('assets_asset_project_id_fkey', 'assets', type_='foreignkey')
    op.drop_constraint('assets_pkey', 'assets', type_='primary')

    op.alter_column('assets', 'asset_id', new_column_name='id')

    op.create_primary_key('assets_pkey', 'assets', ['id'])

    # --- projects table: rename PK ---
    op.drop_constraint('projects_pkey', 'projects', type_='primary')

    op.alter_column('projects', 'project_id', new_column_name='id')

    op.create_primary_key('projects_pkey', 'projects', ['id'])

    # Re-add FK from assets → projects.id
    op.create_foreign_key(
        'assets_asset_project_id_fkey',
        'assets', 'projects',
        ['asset_project_id'], ['id']
    )

    # Re-add FKs from chunks → projects.id and assets.id
    op.create_foreign_key(
        'chunks_chunk_project_id_fkey',
        'chunks', 'projects',
        ['chunk_project_id'], ['id']
    )
    op.create_foreign_key(
        'chunks_chunk_asset_id_fkey',
        'chunks', 'assets',
        ['chunk_asset_id'], ['id']
    )


def downgrade() -> None:
    """Rename id columns back to *_id."""

    # Drop FKs
    op.drop_constraint('chunks_chunk_project_id_fkey', 'chunks', type_='foreignkey')
    op.drop_constraint('chunks_chunk_asset_id_fkey', 'chunks', type_='foreignkey')
    op.drop_constraint('assets_asset_project_id_fkey', 'assets', type_='foreignkey')

    # Rename chunks PK back
    op.drop_constraint('chunks_pkey', 'chunks', type_='primary')
    op.alter_column('chunks', 'id', new_column_name='chunk_id')
    op.create_primary_key('chunks_pkey', 'chunks', ['chunk_id'])

    # Rename assets PK back
    op.drop_constraint('assets_pkey', 'assets', type_='primary')
    op.alter_column('assets', 'id', new_column_name='asset_id')
    op.create_primary_key('assets_pkey', 'assets', ['asset_id'])

    # Rename projects PK back
    op.drop_constraint('projects_pkey', 'projects', type_='primary')
    op.alter_column('projects', 'id', new_column_name='project_id')
    op.create_primary_key('projects_pkey', 'projects', ['project_id'])

    # Re-add old FKs
    op.create_foreign_key(
        'assets_asset_project_id_fkey',
        'assets', 'projects',
        ['asset_project_id'], ['project_id']
    )
    op.create_foreign_key(
        'chunks_chunk_project_id_fkey',
        'chunks', 'projects',
        ['chunk_project_id'], ['project_id']
    )
    op.create_foreign_key(
        'chunks_chunk_asset_id_fkey',
        'chunks', 'assets',
        ['chunk_asset_id'], ['asset_id']
    )

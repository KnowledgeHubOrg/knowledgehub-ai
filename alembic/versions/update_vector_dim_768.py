"""
Revision ID: update_vector_dim_768
Revises: bf901e70df8c
Create Date: 2025-08-18
"""

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision = 'update_vector_dim_768'
down_revision = 'bf901e70df8c'
branch_labels = None
depends_on = None

def upgrade():
    op.execute('ALTER TABLE document_embeddings ALTER COLUMN vector TYPE vector(768);')

def downgrade():
    op.execute('ALTER TABLE document_embeddings ALTER COLUMN vector TYPE vector(384);')

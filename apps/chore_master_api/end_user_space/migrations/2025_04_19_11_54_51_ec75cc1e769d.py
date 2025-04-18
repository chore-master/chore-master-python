"""empty message

Revision ID: ec75cc1e769d
Revises: f46a1ec0f608
Create Date: 2025-04-19 11:54:51.537293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec75cc1e769d'
down_revision = 'f46a1ec0f608'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('finance_transaction',
    sa.Column('reference', sa.String(), nullable=False),
    sa.Column('created_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('portfolio_reference', sa.String(), nullable=False),
    sa.Column('transacted_time', sa.DateTime(), nullable=False),
    sa.Column('chain_id', sa.String(), nullable=True),
    sa.Column('tx_hash', sa.String(), nullable=True),
    sa.Column('remark', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('reference', name=op.f('pk_finance_transaction'))
    )
    with op.batch_alter_table('finance_transaction', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_finance_transaction_created_time'), ['created_time'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_transaction_reference'), ['reference'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_transaction_updated_time'), ['updated_time'], unique=False)

    op.create_table('finance_transfer',
    sa.Column('reference', sa.String(), nullable=False),
    sa.Column('created_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('transaction_reference', sa.String(), nullable=False),
    sa.Column('flow_type', sa.String(), nullable=False),
    sa.Column('asset_amount_change', sa.String(), nullable=False),
    sa.Column('asset_reference', sa.String(), nullable=False),
    sa.Column('settlement_asset_amount_change', sa.String(), nullable=True),
    sa.Column('remark', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('reference', name=op.f('pk_finance_transfer'))
    )
    with op.batch_alter_table('finance_transfer', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_finance_transfer_created_time'), ['created_time'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_transfer_reference'), ['reference'], unique=False)
        batch_op.create_index(batch_op.f('ix_finance_transfer_updated_time'), ['updated_time'], unique=False)

    with op.batch_alter_table('finance_instrument', schema=None) as batch_op:
        batch_op.drop_index('ix_finance_instrument_created_time')
        batch_op.drop_index('ix_finance_instrument_reference')
        batch_op.drop_index('ix_finance_instrument_updated_time')

    op.drop_table('finance_instrument')
    with op.batch_alter_table('finance_fee_entry', schema=None) as batch_op:
        batch_op.drop_index('ix_finance_fee_entry_created_time')
        batch_op.drop_index('ix_finance_fee_entry_reference')
        batch_op.drop_index('ix_finance_fee_entry_updated_time')

    op.drop_table('finance_fee_entry')
    with op.batch_alter_table('finance_ledger_entry', schema=None) as batch_op:
        batch_op.drop_index('ix_finance_ledger_entry_created_time')
        batch_op.drop_index('ix_finance_ledger_entry_reference')
        batch_op.drop_index('ix_finance_ledger_entry_updated_time')

    op.drop_table('finance_ledger_entry')
    with op.batch_alter_table('finance_portfolio', schema=None) as batch_op:
        batch_op.add_column(sa.Column('settlement_asset_reference', sa.String(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('finance_portfolio', schema=None) as batch_op:
        batch_op.drop_column('settlement_asset_reference')

    op.create_table('finance_ledger_entry',
    sa.Column('reference', sa.VARCHAR(), nullable=False),
    sa.Column('created_time', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_time', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('portfolio_reference', sa.VARCHAR(), nullable=False),
    sa.Column('instrument_reference', sa.VARCHAR(), nullable=False),
    sa.Column('entry_type', sa.VARCHAR(), nullable=False),
    sa.Column('source_type', sa.VARCHAR(), nullable=False),
    sa.Column('quantity', sa.INTEGER(), nullable=False),
    sa.Column('price', sa.INTEGER(), nullable=False),
    sa.Column('entry_time', sa.DATETIME(), nullable=False),
    sa.PrimaryKeyConstraint('reference', name='pk_finance_ledger_entry')
    )
    with op.batch_alter_table('finance_ledger_entry', schema=None) as batch_op:
        batch_op.create_index('ix_finance_ledger_entry_updated_time', ['updated_time'], unique=False)
        batch_op.create_index('ix_finance_ledger_entry_reference', ['reference'], unique=False)
        batch_op.create_index('ix_finance_ledger_entry_created_time', ['created_time'], unique=False)

    op.create_table('finance_fee_entry',
    sa.Column('reference', sa.VARCHAR(), nullable=False),
    sa.Column('created_time', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_time', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('ledger_entry_reference', sa.VARCHAR(), nullable=False),
    sa.Column('fee_type', sa.VARCHAR(), nullable=False),
    sa.Column('amount', sa.INTEGER(), nullable=False),
    sa.Column('asset_reference', sa.VARCHAR(), nullable=False),
    sa.PrimaryKeyConstraint('reference', name='pk_finance_fee_entry')
    )
    with op.batch_alter_table('finance_fee_entry', schema=None) as batch_op:
        batch_op.create_index('ix_finance_fee_entry_updated_time', ['updated_time'], unique=False)
        batch_op.create_index('ix_finance_fee_entry_reference', ['reference'], unique=False)
        batch_op.create_index('ix_finance_fee_entry_created_time', ['created_time'], unique=False)

    op.create_table('finance_instrument',
    sa.Column('reference', sa.VARCHAR(), nullable=False),
    sa.Column('created_time', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_time', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('user_reference', sa.VARCHAR(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.Column('quantity_decimals', sa.INTEGER(), nullable=False),
    sa.Column('price_decimals', sa.INTEGER(), nullable=False),
    sa.Column('instrument_type', sa.VARCHAR(), nullable=False),
    sa.Column('base_asset_reference', sa.VARCHAR(), nullable=True),
    sa.Column('quote_asset_reference', sa.VARCHAR(), nullable=True),
    sa.Column('settlement_asset_reference', sa.VARCHAR(), nullable=True),
    sa.Column('underlying_asset_reference', sa.VARCHAR(), nullable=True),
    sa.Column('staking_asset_reference', sa.VARCHAR(), nullable=True),
    sa.Column('yielding_asset_reference', sa.VARCHAR(), nullable=True),
    sa.PrimaryKeyConstraint('reference', name='pk_finance_instrument')
    )
    with op.batch_alter_table('finance_instrument', schema=None) as batch_op:
        batch_op.create_index('ix_finance_instrument_updated_time', ['updated_time'], unique=False)
        batch_op.create_index('ix_finance_instrument_reference', ['reference'], unique=False)
        batch_op.create_index('ix_finance_instrument_created_time', ['created_time'], unique=False)

    with op.batch_alter_table('finance_transfer', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_finance_transfer_updated_time'))
        batch_op.drop_index(batch_op.f('ix_finance_transfer_reference'))
        batch_op.drop_index(batch_op.f('ix_finance_transfer_created_time'))

    op.drop_table('finance_transfer')
    with op.batch_alter_table('finance_transaction', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_finance_transaction_updated_time'))
        batch_op.drop_index(batch_op.f('ix_finance_transaction_reference'))
        batch_op.drop_index(batch_op.f('ix_finance_transaction_created_time'))

    op.drop_table('finance_transaction')
    # ### end Alembic commands ###

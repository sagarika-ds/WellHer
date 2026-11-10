"""initial schema

Revision ID: 0001
Revises: 
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import app.core.crypto
import app.db.base

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS citext')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.create_table('users',
    sa.Column('email', app.db.base.CIText(), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.Column('role', sa.String(length=20), server_default='user', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role in ('user','admin')", name=op.f('ck_users_role_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_table('ai_settings',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('personalization_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('external_llm_allowed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('context_allowlist', sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('chat_retention_days', sa.Integer(), server_default='30', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('chat_retention_days between 0 and 365', name=op.f('ck_ai_settings_retention_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ai_settings_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_ai_settings'))
    )
    op.create_table('audit_logs',
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('action', sa.String(length=60), nullable=False),
    sa.Column('resource', sa.String(length=60), nullable=True),
    sa.Column('resource_id', sa.String(length=64), nullable=True),
    sa.Column('outcome', sa.String(length=10), server_default='success', nullable=False),
    sa.Column('ip', sa.String(length=64), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('request_id', sa.String(length=64), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_logs_user_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index('ix_audit_logs_user_id_occurred_at', 'audit_logs', ['user_id', sa.literal_column('occurred_at DESC')], unique=False)
    op.create_table('cycle_records',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('flow_intensity', sa.SmallInteger(), nullable=True),
    sa.Column('notes', app.core.crypto.EncryptedText(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_date is null or end_date >= start_date', name=op.f('ck_cycle_records_end_after_start')),
    sa.CheckConstraint('flow_intensity is null or flow_intensity between 1 and 5', name=op.f('ck_cycle_records_flow_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_cycle_records_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cycle_records')),
    sa.UniqueConstraint('user_id', 'start_date', name=op.f('uq_cycle_records_user_id_start_date'))
    )
    op.create_index('ix_cycle_records_user_id_start_date_desc', 'cycle_records', ['user_id', sa.literal_column('start_date DESC')], unique=False)
    op.create_table('health_profiles',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('height_cm', sa.Numeric(precision=5, scale=1), nullable=True),
    sa.Column('weight_kg', sa.Numeric(precision=5, scale=1), nullable=True),
    sa.Column('typical_cycle_length', sa.SmallInteger(), nullable=True),
    sa.Column('contraceptive_use', sa.Boolean(), nullable=True),
    sa.Column('conditions_self_reported', app.core.crypto.EncryptedText(), nullable=True),
    sa.Column('activity_level', sa.String(length=20), nullable=True),
    sa.Column('dietary_prefs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('goals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('height_cm is null or height_cm between 50 and 250', name=op.f('ck_health_profiles_height_range')),
    sa.CheckConstraint('typical_cycle_length is null or typical_cycle_length between 15 and 90', name=op.f('ck_health_profiles_cycle_len_range')),
    sa.CheckConstraint('weight_kg is null or weight_kg between 20 and 400', name=op.f('ck_health_profiles_weight_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_health_profiles_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_health_profiles'))
    )
    op.create_table('lifestyle_records',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('sleep_hours', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('sleep_quality', sa.SmallInteger(), nullable=True),
    sa.Column('activity_minutes', sa.Integer(), nullable=True),
    sa.Column('water_ml', sa.Integer(), nullable=True),
    sa.Column('stress_level', sa.SmallInteger(), nullable=True),
    sa.Column('nutrition_notes', app.core.crypto.EncryptedText(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('activity_minutes is null or activity_minutes between 0 and 1440', name=op.f('ck_lifestyle_records_activity_range')),
    sa.CheckConstraint('sleep_hours is null or sleep_hours between 0 and 24', name=op.f('ck_lifestyle_records_sleep_range')),
    sa.CheckConstraint('sleep_quality is null or sleep_quality between 1 and 5', name=op.f('ck_lifestyle_records_sleepq_range')),
    sa.CheckConstraint('stress_level is null or stress_level between 1 and 5', name=op.f('ck_lifestyle_records_stress_range')),
    sa.CheckConstraint('water_ml is null or water_ml between 0 and 20000', name=op.f('ck_lifestyle_records_water_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_lifestyle_records_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lifestyle_records')),
    sa.UniqueConstraint('user_id', 'date', name=op.f('uq_lifestyle_records_user_id_date'))
    )
    op.create_index('ix_lifestyle_records_user_id_date_desc', 'lifestyle_records', ['user_id', sa.literal_column('date DESC')], unique=False)
    op.create_table('mood_records',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('mood_score', sa.SmallInteger(), nullable=False),
    sa.Column('tags', sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('mood_score between 1 and 5', name=op.f('ck_mood_records_mood_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mood_records_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mood_records'))
    )
    op.create_index('ix_mood_records_user_id_logged_at_desc', 'mood_records', ['user_id', sa.literal_column('logged_at DESC')], unique=False)
    op.create_table('password_reset_tokens',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_password_reset_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_password_reset_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_password_reset_tokens_token_hash'))
    )
    op.create_index(op.f('ix_password_reset_tokens_user_id'), 'password_reset_tokens', ['user_id'], unique=False)
    op.create_table('pipeline_runs',
    sa.Column('event_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=60), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('handler', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='1', nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint("status in ('running','done','failed')", name=op.f('ck_pipeline_runs_status_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_pipeline_runs_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pipeline_runs')),
    sa.UniqueConstraint('event_id', 'handler', name=op.f('uq_pipeline_runs_event_id_handler'))
    )
    op.create_table('refresh_tokens',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('family_id', sa.UUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('device', sa.String(length=100), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('replaced_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_tokens_token_hash'))
    )
    op.create_index('ix_refresh_tokens_user_id_family_id', 'refresh_tokens', ['user_id', 'family_id'], unique=False)
    op.create_table('timeline_events',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('source_table', sa.String(length=40), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_timeline_events_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_timeline_events')),
    sa.UniqueConstraint('source_table', 'source_id', name=op.f('uq_timeline_events_source_table_source_id'))
    )
    op.create_index('ix_timeline_events_user_id_occurred_at_desc', 'timeline_events', ['user_id', sa.literal_column('occurred_at DESC')], unique=False)
    op.create_table('user_consents',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('purpose', sa.String(length=30), nullable=False),
    sa.Column('granted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('version', sa.String(length=20), nullable=False),
    sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("purpose in ('health_tracking', 'ml_processing', 'llm_external', 'analytics')", name=op.f('ck_user_consents_purpose_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_consents_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_consents')),
    sa.UniqueConstraint('user_id', 'purpose', name=op.f('uq_user_consents_user_id_purpose'))
    )
    op.create_table('symptom_logs',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('symptom_code', sa.String(length=40), nullable=False),
    sa.Column('severity', sa.SmallInteger(), nullable=False),
    sa.Column('cycle_id', sa.UUID(), nullable=True),
    sa.Column('source', sa.String(length=15), server_default='manual', nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("source in ('manual','conversation','import')", name=op.f('ck_symptom_logs_source_valid')),
    sa.CheckConstraint('severity between 1 and 5', name=op.f('ck_symptom_logs_severity_range')),
    sa.ForeignKeyConstraint(['cycle_id'], ['cycle_records.id'], name=op.f('fk_symptom_logs_cycle_id_cycle_records'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_symptom_logs_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_symptom_logs'))
    )
    op.create_index('ix_symptom_logs_user_id_logged_at_desc', 'symptom_logs', ['user_id', sa.literal_column('logged_at DESC')], unique=False)

    # Append-only audit log. Allowed: INSERT, and the UPDATE that nulls user_id when an account is erased.
    op.execute("""
        CREATE FUNCTION audit_logs_append_only() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'audit_logs is append-only';
          END IF;
          IF NEW.user_id IS NOT NULL
             OR (to_jsonb(NEW) - 'user_id') IS DISTINCT FROM (to_jsonb(OLD) - 'user_id') THEN
            RAISE EXCEPTION 'audit_logs is append-only';
          END IF;
          RETURN NEW;
        END $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_logs_append_only BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_append_only()
    """)


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs')
    op.execute('DROP FUNCTION IF EXISTS audit_logs_append_only()')
    op.drop_index('ix_symptom_logs_user_id_logged_at_desc', table_name='symptom_logs')
    op.drop_table('symptom_logs')
    op.drop_table('user_consents')
    op.drop_index('ix_timeline_events_user_id_occurred_at_desc', table_name='timeline_events')
    op.drop_table('timeline_events')
    op.drop_index('ix_refresh_tokens_user_id_family_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('pipeline_runs')
    op.drop_index(op.f('ix_password_reset_tokens_user_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_index('ix_mood_records_user_id_logged_at_desc', table_name='mood_records')
    op.drop_table('mood_records')
    op.drop_index('ix_lifestyle_records_user_id_date_desc', table_name='lifestyle_records')
    op.drop_table('lifestyle_records')
    op.drop_table('health_profiles')
    op.drop_index('ix_cycle_records_user_id_start_date_desc', table_name='cycle_records')
    op.drop_table('cycle_records')
    op.drop_index('ix_audit_logs_user_id_occurred_at', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_table('ai_settings')
    op.drop_table('users')

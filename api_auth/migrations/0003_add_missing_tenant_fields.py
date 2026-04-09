# Generated manually to fix missing tenant columns in production
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_auth', '0002_alter_refreshtoken_token'),
    ]

    operations = [
        # Add tenant field to RefreshToken if it doesn't exist
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='api_auth_refreshtoken' AND column_name='tenant'
                ) THEN
                    ALTER TABLE api_auth_refreshtoken
                    ADD COLUMN tenant VARCHAR(100) NULL;
                END IF;
            END $$;
            """,
            reverse_sql="SELECT 1;",  # No-op for reverse
        ),
        # Add tenant field to AccessTokenLog if it doesn't exist
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='api_auth_accesstokenlog' AND column_name='tenant'
                ) THEN
                    ALTER TABLE api_auth_accesstokenlog
                    ADD COLUMN tenant VARCHAR(100) NULL;
                END IF;
            END $$;
            """,
            reverse_sql="SELECT 1;",
        ),
        # Add tenant field to DeviceRegistration if it doesn't exist
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='api_auth_deviceregistration' AND column_name='tenant'
                ) THEN
                    ALTER TABLE api_auth_deviceregistration
                    ADD COLUMN tenant VARCHAR(100) NULL;
                END IF;
            END $$;
            """,
            reverse_sql="SELECT 1;",
        ),
        # Add tenant field to PKCESession if it doesn't exist
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='api_auth_pkcesession' AND column_name='tenant'
                ) THEN
                    ALTER TABLE api_auth_pkcesession
                    ADD COLUMN tenant VARCHAR(100) NULL;
                END IF;
            END $$;
            """,
            reverse_sql="SELECT 1;",
        ),
    ]

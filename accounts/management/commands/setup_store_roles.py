from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

from accounts.roles import STORE_ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Create the standard Delhi Stationery staff groups and permissions."

    def handle(self, *args, **options):
        permission_refs = set().union(*STORE_ROLE_PERMISSIONS.values())
        permission_map = {}
        missing = []

        for permission_ref in sorted(permission_refs):
            app_label, codename = permission_ref.split(".", 1)
            permissions = list(
                Permission.objects.filter(
                    content_type__app_label=app_label,
                    codename=codename,
                )
            )
            if not permissions:
                missing.append(permission_ref)
            else:
                permission_map[permission_ref] = permissions

        if missing:
            raise CommandError(
                "Missing staff permissions. Run migrations first: "
                + ", ".join(missing)
            )

        for role_name, permission_names in STORE_ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            permissions = [
                permission
                for permission_name in permission_names
                for permission in permission_map[permission_name]
            ]
            group.permissions.add(*permissions)
            self.stdout.write(f"Configured {role_name}.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Configured {len(STORE_ROLE_PERMISSIONS)} store staff roles."
            )
        )

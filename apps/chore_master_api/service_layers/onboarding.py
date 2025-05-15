from apps.chore_master_api.end_user_space.models.identity import UserAttribute, UserRole
from apps.chore_master_api.end_user_space.models.trace import Quota
from apps.chore_master_api.end_user_space.unit_of_works.identity import (
    IdentitySQLAlchemyUnitOfWork,
)
from apps.chore_master_api.end_user_space.unit_of_works.trace import (
    TraceSQLAlchemyUnitOfWork,
)

# async def ensure_system_initialized(
#     chore_master_db: RelationalDatabase,
#     chore_master_db_registry: registry,
#     schema_migration: SchemaMigration,
# ):
#     try:
#         applied_revision = schema_migration.applied_revision(
#             metadata=chore_master_db_registry.metadata
#         )
#         if applied_revision is not None:
#             return
#     except alembic.util.exc.CommandError as e:
#         if str(e).startswith("Can't locate revision identified by"):
#             # 當實際版本無法匹配任一 scripts 的版本時
#             await chore_master_db.drop_tables(
#                 metadata=chore_master_db_registry.metadata
#             )
#         else:
#             raise NotImplementedError

#     all_revisions = schema_migration.all_revisions(
#         metadata=chore_master_db_registry.metadata
#     )
#     if len(all_revisions) == 0:
#         await chore_master_db.drop_tables(metadata=chore_master_db_registry.metadata)
#         schema_migration.generate_revision(metadata=chore_master_db_registry.metadata)
#     schema_migration.upgrade(metadata=chore_master_db_registry.metadata)

#     data_migration = DataMigration(chore_master_db, chore_master_db_registry)

#     for directory in ["global", "admin"]:
#         await data_migration.import_files(
#             [
#                 (
#                     file_path.split("/")[-1],
#                     open(file_path, "rb"),
#                 )
#                 for file_path in FileSystemUtils.match_paths(
#                     f"apps/chore_master_api/end_user_space/data/{directory}/delete/**/*.csv",
#                     recursive=True,
#                 )
#             ]
#         )
#         await data_migration.import_files(
#             [
#                 (
#                     file_path.split("/")[-1],
#                     open(file_path, "rb"),
#                 )
#                 for file_path in FileSystemUtils.match_paths(
#                     f"apps/chore_master_api/end_user_space/data/{directory}/insert/**/*.csv",
#                     recursive=True,
#                 )
#             ]
#         )


async def ensure_user_initialized(
    identity_uow: IdentitySQLAlchemyUnitOfWork,
    trace_uow: TraceSQLAlchemyUnitOfWork,
    user_reference: str,
    user_attributes: dict[str, str],
):
    user_roles = await identity_uow.user_role_repository.find_many(
        filter={"user_reference": user_reference}
    )
    if len(user_roles) == 0:
        roles = await identity_uow.role_repository.find_many()
        await identity_uow.user_role_repository.insert_many(
            [
                UserRole(
                    user_reference=user_reference,
                    role_reference=role.reference,
                )
                for role in roles
                if role.symbol in {"GUEST", "FREEMIUM"}
            ]
        )

    if len(user_attributes) > 0:
        existing_user_attributes = (
            await identity_uow.user_attribute_repository.find_many(
                filter={"user_reference": user_reference}
            )
        )
        existing_user_attribute_key_to_reference_map = {
            existing_user_attribute.key: existing_user_attribute.reference
            for existing_user_attribute in existing_user_attributes
        }

        for user_attribute_key, user_attribute_value in user_attributes.items():
            if user_attribute_key in existing_user_attribute_key_to_reference_map:
                existing_user_attribute_reference = (
                    existing_user_attribute_key_to_reference_map[user_attribute_key]
                )
                await identity_uow.user_attribute_repository.update_many(
                    filter={"reference": existing_user_attribute_reference},
                    values={"value": user_attribute_value},
                )
            else:
                await identity_uow.user_attribute_repository.insert_one(
                    UserAttribute(
                        user_reference=user_reference,
                        key=user_attribute_key,
                        value=user_attribute_value,
                    )
                )

    quotas = await trace_uow.quota_repository.find_many(
        filter={"user_reference": user_reference}
    )
    if len(quotas) == 0:
        quota = Quota(
            user_reference=user_reference,
            limit=100,
            used=0,
        )
        await trace_uow.quota_repository.insert_one(quota)
